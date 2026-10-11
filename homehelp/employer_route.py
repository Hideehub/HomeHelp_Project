import secrets,requests
from datetime import datetime
from decimal import Decimal
from flask import render_template,request,redirect,flash,session,url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message

from homehelp import app,mail
from homehelp.models import db,Employer,Withdrawal,Worker,EmployerRecipient,Review,JobPosting,Payment
from homehelp.forms import LoginForm,SigninForm
from homehelp.utils import save_image, parse_amount

PAYSTACK_API = 'https://api.paystack.co'


def paystack_headers():
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {app.config['PAYSTACK_SECRET_KEY']}"
    }


def to_kobo(amount):
    return int((Decimal(amount) * 100).quantize(Decimal('1')))


def unused_payment(employer_id, worker_id, lock=False):
    """A verified payment from this employer to this worker that is not yet attached to a job."""
    query = (
        db.session.query(Payment)
        .outerjoin(JobPosting, JobPosting.post_payid == Payment.pay_id)
        .filter(
            Payment.pay_employerid == employer_id,
            Payment.pay_workerid == worker_id,
            Payment.pay_status == 'paid',
            JobPosting.post_id.is_(None)
        )
        .order_by(Payment.pay_id.desc())
    )
    if lock:
        query = query.with_for_update()
    return query.first()



@app.route("/registration/")
def register():
    return render_template('employer/registration.html')


@app.route('/login/',methods=["GET","POST"])
def login():
    loginform = LoginForm()
    if request.method == "GET":
        return render_template('employer/login.html',loginform=loginform)
    else:
        if loginform.validate_on_submit():
            email = loginform.email.data
            password = loginform.password.data

            record = db.session.query(Employer).filter(Employer.employer_email == email).first()
            if not record or not check_password_hash(record.employer_password, password):
                flash('errormsg', 'Invalid email or password')
                return redirect('/login/')

            if record.employer_status == "inactive":
                flash('errormsg', 'Your account is inactive. Please contact admin.')
                return redirect('/login/')

            # Start a fresh session so no other role's login carries over
            session.clear()
            session['role'] = 'employer'
            session['loggedin'] = record.employer_id
            return redirect('/all/helpers/')

        flash('errormsg', 'Invalid form submission, Please fill in all fields')
    return redirect('/login/')



@app.route('/signup/', methods=['POST', 'GET'])
def signup():
    signinform = SigninForm()
    if request.method == 'GET':
        return render_template('employer/signup.html', signinform=signinform)

    if signinform.validate_on_submit():
        email = signinform.email.data

        if signinform.state.data == '0':
            flash('errormsg', 'Please select a valid state.')
            return render_template('employer/signup.html', signinform=signinform)

        if signinform.password.data != signinform.cpassword.data:
            flash('errormsg','Password mismatch, please ensure you enter the password correctly')
            return render_template('employer/signup.html', signinform=signinform)

        if Employer.query.filter_by(employer_email=email).first():
                flash("errormsg", "Already have an account, Please use a different email.")
                return render_template('employer/signup.html', signinform=signinform)

        hashed_password = generate_password_hash(signinform.password.data, method='pbkdf2:sha256')
        new_employer = Employer(
            employer_name=signinform.name.data,
            employer_password=hashed_password,
            employer_email=signinform.email.data,
            employer_phoneno=signinform.phone.data,
            employer_gender=signinform.gender.data,
            employer_address=signinform.address.data,
            employer_stateid=signinform.state.data,
            employer_status='active'
        )
        db.session.add(new_employer)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            app.logger.exception("Employer signup failed")
            flash('errormsg', 'An error occurred while creating your account. Please try again.')
            return render_template('employer/signup.html', signinform=signinform)

        flash('success', 'An account has been created for you!')
        return redirect('/login/')

    for field, errors in signinform.errors.items():
        for error in errors:
            flash('errormsg', f"Error in {getattr(signinform, field).label.text}: {error}")
    return render_template('employer/signup.html', signinform=signinform)



@app.route('/all/helpers/', methods=["POST", "GET"])
def helpers():
    loggedin_employer = session.get('loggedin')
    if loggedin_employer:
        employer_deets = db.session.query(Employer).get(loggedin_employer)

        worker_deets = db.session.query(Worker).all()

        worker_data = []
        for worker in worker_deets:
            worker_data.append({
                'worker': worker,
                'experiences': worker.experiences if worker.experiences else [],
                'state': worker.state.state_name if worker.state else "Not specified",
                'category': worker.category,
                'reviews': worker.reviews_as_worker if worker.reviews_as_worker else []
            })
        return render_template(
            'employer/all_helpers.html',
            employer_deets=employer_deets,
            worker_data=worker_data,
            worker_deets=worker_deets
        )

    else:
        flash('errormsg', 'You must be logged in.')
        return redirect("/login/")



@app.route("/employer/dashboard/")
def dashboard():
    loggedin_employer = session.get('loggedin')
    if loggedin_employer:
        employer_deets = db.session.query(Employer).get(loggedin_employer)
        job_postings = JobPosting.query.filter_by(post_employerid=employer_deets.employer_id).all()
        return render_template("employer/dashboard.html", employer_deets=employer_deets, job_postings=job_postings)
    else:
        flash('errormsg', "You must be logged in")
        return redirect('/login/')



@app.route('/employer/profile/')
def employer_profile():
    loggedin_employer = session.get('loggedin')
    if loggedin_employer:
        employer_deets = db.session.query(Employer).get(loggedin_employer)
        return render_template('employer/profile.html',employer_deets=employer_deets)
    else:
        flash('errormsg', 'You must be loggedin')
        return redirect("/login/")



@app.route('/profile/<employer_id>/update/',methods=["GET",'POST'])
def update_profile(employer_id):
    loggedin_employer = session.get('loggedin')
    if loggedin_employer:
        # Always edit the logged-in employer, never the id in the URL
        employer_deets = db.session.query(Employer).get(loggedin_employer)

        if request.method == "POST":
            filename = save_image(request.files.get('employer_picture'))
            if filename is False:
                flash('errormsg', 'Your cover image must be an image file')
                return redirect('/employer/profile/')

            employer_deets.employer_name = request.form.get('name') or employer_deets.employer_name
            employer_deets.employer_phoneno = request.form.get('phone') or employer_deets.employer_phoneno
            employer_deets.employer_address = request.form.get('address') or employer_deets.employer_address
            if filename:
                employer_deets.employer_picture = filename
            db.session.commit()
            flash("feedback", "Profile details updated successfully!")
            return redirect('/employer/profile/')
        else:
            return redirect('/employer/profile/')
    else:
        flash('errormsg', 'You must be loggedin')
        return redirect("/login/")



@app.route('/payment/<int:worker_id>', methods=['GET', 'POST'])
def make_payment(worker_id):
    loggedin_employer = session.get('loggedin')
    if not loggedin_employer:
        flash('errormsg', "You must be logged in")
        return redirect('/login/')

    worker = db.session.query(Worker).get(worker_id)
    if not worker:
        flash("errormsg", "Worker not found.")
        return redirect('/employer/dashboard/')

    if request.method == 'GET':
        employer_deets = db.session.query(Employer).get(loggedin_employer)
        return render_template('employer/payment.html',
                               employer_deets=employer_deets,
                               worker=worker)
    else:
        if not worker.worker_price or worker.worker_price <= 0:
            flash("errormsg", "This helper has not set a valid price yet.")
            return redirect(url_for('helpers'))
        ref = f'HH-{secrets.token_hex(10)}'
        session['refno'] = ref
        pay = Payment(pay_employerid=loggedin_employer, pay_amount=worker.worker_price, pay_ref=ref, pay_workerid=worker_id, pay_date=datetime.utcnow())
        db.session.add(pay)
        db.session.commit()
        return redirect(url_for('payment_confirmation', worker_id=worker_id))



@app.route('/pay/confirm/<int:worker_id>', methods=['GET', 'POST'])
def payment_confirmation(worker_id):
    loggedin_employer = session.get('loggedin')
    if not loggedin_employer:
        flash("errormsg","Please start the transaction from here")
        return redirect("/login/")

    employer_deets = db.session.query(Employer).get(loggedin_employer)
    refno = session.get('refno')
    if not refno:
        flash("errormsg", "Please start transaction from here")
        return redirect(url_for('make_payment', worker_id=worker_id))

    trxdeets = db.session.query(Payment).filter(
        Payment.pay_ref == refno,
        Payment.pay_employerid == loggedin_employer,
        Payment.pay_workerid == worker_id,
        Payment.pay_status == 'pending'
    ).first()
    if not trxdeets:
        flash("errormsg", "Transaction details not found." )
        return redirect(url_for('make_payment', worker_id=worker_id))

    if request.method == 'GET':
        return render_template('employer/payment_confirm.html',
                               payment_deets=trxdeets,
                               trxdeets=trxdeets,
                               employer_deets=employer_deets,
                               worker=db.session.query(Worker).get(worker_id))
    else:
        # POST: Connect to Paystack to initialize the transaction.
        data = {
            "reference": refno,
            "amount": to_kobo(trxdeets.pay_amount),
            "email": trxdeets.employer.employer_email,
            "callback_url": url_for('paystack_update', _external=True)
        }
        try:
            response = requests.post(f'{PAYSTACK_API}/transaction/initialize', headers=paystack_headers(), json=data, timeout=15)
            json_response = response.json()
        except (requests.RequestException, ValueError):
            app.logger.exception("Paystack initialize failed")
            flash("errormsg", "Could not reach the payment gateway, please try again.")
            return redirect(url_for('make_payment', worker_id=worker_id))

        if json_response.get("status"):
            authurl = json_response['data']['authorization_url']
            return redirect(authurl)
        else:
            flash("errormsg", json_response.get("message", "Error connecting to payment gateway"))
            return redirect(url_for('make_payment', worker_id=worker_id))




@app.route('/payment/update/', methods=['GET'])
def paystack_update():
    loggedin_employer = session.get('loggedin')
    if not loggedin_employer:
        flash("errormsg", "Please log in to complete your payment.")
        return redirect('/login/')

    refno = request.args.get('reference') or session.get('refno')
    pay = db.session.query(Payment).filter(
        Payment.pay_ref == refno,
        Payment.pay_employerid == loggedin_employer
    ).first() if refno else None
    if not pay:
        flash("errormsg", "Transaction could not be verified.")
        return redirect(url_for('helpers'))

    # Already verified (e.g. page refreshed): don't verify again
    if pay.pay_status != 'pending':
        if pay.pay_status == 'paid':
            return redirect(url_for('job_description_form', worker_id=pay.pay_workerid))
        flash("errormsg", "This transaction is no longer valid. Please start a new payment.")
        return redirect(url_for('make_payment', worker_id=pay.pay_workerid))

    try:
        response = requests.get(f'{PAYSTACK_API}/transaction/verify/{refno}', headers=paystack_headers(), timeout=15)
        rsp = response.json()
    except (requests.RequestException, ValueError):
        app.logger.exception("Paystack verify failed")
        flash("errormsg", "Paystack is unavailable, please refresh this page in a moment.")
        return redirect(url_for('make_payment', worker_id=pay.pay_workerid))

    data = rsp.get('data') or {}
    # rsp['status'] only means the API call worked; data['status'] is the payment outcome
    succeeded = (
        rsp.get('status') is True
        and data.get('status') == 'success'
        and data.get('reference') == refno
        and data.get('amount') == to_kobo(pay.pay_amount)
    )
    pay.pay_data = data.get('gateway_response') or rsp.get('message')
    if succeeded:
        pay.pay_status = 'paid'
        db.session.commit()
        session.pop('refno', None)
        return redirect(url_for('job_description_form', worker_id=pay.pay_workerid))

    if data.get('status') in ('failed', 'abandoned', 'reversed'):
        pay.pay_status = 'failed'
    db.session.commit()
    flash("errormsg", "Payment was not completed: " + (pay.pay_data or "unknown reason"))
    return redirect(url_for('make_payment', worker_id=pay.pay_workerid))



@app.route('/job/description/<int:worker_id>', methods=['GET'])
def job_description_form(worker_id):
    loggedin_employer = session.get('loggedin')
    if not loggedin_employer:
         flash("errormsg", "You must be logged in")
         return redirect('/login/')
    employer_deets = db.session.query(Employer).get(loggedin_employer)
    worker = db.session.query(Worker).get(worker_id)
    if not worker:
         flash("errormsg", "Worker not found.")
         return redirect('/employer/dashboard/')
    if not unused_payment(loggedin_employer, worker_id):
        flash("errormsg", "Please pay for this helper before sending a job.")
        return redirect(url_for('make_payment', worker_id=worker_id))
    return render_template('employer/job_description.html',
                           employer_deets=employer_deets,
                           worker=worker)



@app.route('/send-job-description/', methods=['POST'])
def send_job_description():
    employer_id = session.get('loggedin')
    if not employer_id:
        flash("errormsg", "You must be logged in")
        return redirect('/login/')

    post_description = (request.form.get('job_description') or '').strip()
    try:
        worker_id = int(request.form.get('worker_id'))
    except (TypeError, ValueError):
        flash("errormsg", "Worker not found.")
        return redirect(url_for('helpers'))

    if not post_description:
        flash("errormsg", "Please provide a job description.")
        return redirect(url_for('job_description_form', worker_id=worker_id))

    worker = db.session.query(Worker).get(worker_id)
    if not worker:
        flash("errormsg","Worker not found.")
        return redirect(url_for('helpers'))

    payment = unused_payment(employer_id, worker_id, lock=True)
    if not payment:
        db.session.rollback()
        flash("errormsg", "Please pay for this helper before sending a job.")
        return redirect(url_for('make_payment', worker_id=worker_id))

    try:
        new_job = JobPosting(
            post_workerid=worker.worker_id,
            post_employerid=employer_id,
            post_description=post_description,
            post_categoryid=worker.worker_categoryid,
            post_title=worker.category.cat_name if worker.category else None,
            post_payrate=payment.pay_amount,
            post_dateadded=datetime.utcnow(),
            post_payid=payment.pay_id
        )
        db.session.add(new_job)
        db.session.commit()
    except Exception:
        db.session.rollback()
        app.logger.exception("Saving job posting failed")
        flash("errormsg", "An error occurred while saving the job description. Please try again.")
        return redirect(url_for('job_description_form', worker_id=worker_id))

    subject = "New Job Opportunity from HomeHelp"
    body = f"""
    Hello {worker.worker_fname} {worker.worker_lname},
    You have received a new job description:
    {post_description}

    Please log in to your account for more details.

    Best regards,
    HomeHelp Team
    """
    msg = Message(subject, recipients=[worker.worker_email])
    msg.body = body
    try:
        mail.send(msg)
    except Exception:
        app.logger.exception("Sending job email failed")
        flash("errormsg", "Job saved, but the email notification to the helper could not be sent.")
        return redirect(url_for('dashboard'))

    flash( "success", "Job description sent successfully!")
    return redirect(url_for('dashboard'))


@app.route('/job/cancel/<int:post_id>', methods=['POST'])
def cancel_job(post_id):
    loggedin_employer = session.get('loggedin')
    if not loggedin_employer:
        flash("errormsg", "You must be logged in")
        return redirect(url_for('login'))

    job = db.session.query(JobPosting).with_for_update().filter_by(post_id=post_id).first()

    if not job or job.post_employerid != loggedin_employer:
        db.session.rollback()
        flash("errormsg", "Job not found")
        return redirect(url_for('dashboard'))

    if job.post_status not in ['0', '1']:
        db.session.rollback()
        flash("errormsg", "Job cannot be cancelled at this stage")
        return redirect(url_for('dashboard'))

    job.post_status = '4'

    # Refund only the payment that funded this job, and only once
    payment = job.payment
    refunded = False
    if payment and payment.pay_status == 'paid':
        employer = db.session.get(Employer, loggedin_employer, with_for_update=True)
        employer.employer_walletbalance = (employer.employer_walletbalance or Decimal('0')) + payment.pay_amount
        payment.pay_status = 'refunded'
        refunded = True

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        app.logger.exception("Cancelling job failed")
        flash("errormsg", "Error cancelling the job. Please try again.")
        return redirect(url_for('dashboard'))

    if refunded:
        flash("success", "Job cancelled and payment refunded to your wallet for manual withdrawal.")
    else:
        flash("success", "Job cancelled.")
    return redirect(url_for('dashboard'))




@app.route('/job/complete/<int:post_id>', methods=['POST'])
def complete_job(post_id):
    loggedin_employer = session.get('loggedin')
    if not loggedin_employer:
        flash("errormsg", "You must be logged in")
        return redirect(url_for('login'))

    job = db.session.query(JobPosting).with_for_update().filter_by(post_id=post_id).first()
    if not job or job.post_employerid != loggedin_employer:
        db.session.rollback()
        flash("errormsg", "Job not found")
        return redirect(url_for('dashboard'))

    # Only a job the helper has accepted can be completed
    if job.post_status != '1':
        db.session.rollback()
        flash("errormsg", "Only accepted jobs can be marked as completed.")
        return redirect(url_for('dashboard'))

    job.post_status = "3"

    payment = job.payment
    credited = False
    if payment and payment.pay_status == 'paid':
        worker = db.session.get(Worker, job.post_workerid, with_for_update=True)
        if worker:
            worker.worker_walletbalance = (worker.worker_walletbalance or Decimal('0')) + payment.pay_amount
            payment.pay_status = 'credited'
            credited = True

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        app.logger.exception("Completing job failed")
        flash("errormsg", "Error completing the job. Please try again.")
        return redirect(url_for('dashboard'))

    if credited:
        flash("success", "Job completed and payout initiated. The funds have been added to the worker's wallet.")
    else:
        flash("success", "Job marked as completed.")
    return redirect(url_for('dashboard'))



@app.route('/employer/wallet/', methods=['GET', 'POST'])
def employer_wallet():
    loggedin_employer = session.get('loggedin')
    if not loggedin_employer:
        flash("errormsg", "You must be logged in")
        return redirect(url_for('login'))
    if request.method == 'GET':
        employer_deets = db.session.query(Employer).get(loggedin_employer)
        return render_template('employer/employer_wallet.html', employer_deets=employer_deets)

    amount = parse_amount(request.form.get('amount'))
    if amount is None:
        flash("errormsg", "Invalid withdrawal amount.")
        return redirect(url_for('employer_wallet'))

    recipient = db.session.query(EmployerRecipient).filter_by(emprecp_employerid=loggedin_employer).first()
    if not recipient:
        flash("errormsg", "Please add your bank details first.")
        return redirect(url_for('update_bankdetails'))

    # Lock the row so two simultaneous requests can't both spend the same balance
    employer_deets = db.session.get(Employer, loggedin_employer, with_for_update=True)
    balance = employer_deets.employer_walletbalance or Decimal('0')
    if amount > balance:
        db.session.rollback()
        flash("errormsg", "Insufficient funds.")
        return redirect(url_for('employer_wallet'))

    employer_deets.employer_walletbalance = balance - amount

    new_withdrawal = Withdrawal(
        withdraw_userid=loggedin_employer,
        withdraw_usertype='employer',
        withdraw_amount=amount,
        withdraw_status='pending'
    )
    db.session.add(new_withdrawal)

    try:
        db.session.commit()
        flash("success", "Withdrawal request submitted. Your funds will be processed manually.")
    except Exception:
        db.session.rollback()
        app.logger.exception("Employer withdrawal failed")
        flash("errormsg", "Error processing withdrawal. Please try again.")

    return redirect(url_for('employer_wallet'))



@app.route('/update_bankdetails/', methods=['GET', 'POST'])
def update_bankdetails():
    loggedin_employer = session.get('loggedin')
    if not loggedin_employer:
        flash("errormsg", "You must be logged in as an employer.")
        return redirect(url_for('login'))

    if request.method == 'GET':
        employer_deets = db.session.query(Employer).get(loggedin_employer)
        recipient = db.session.query(EmployerRecipient).filter_by(emprecp_employerid=loggedin_employer).first()
        return render_template('employer/bank_details.html',recipient=recipient, employer_deets= employer_deets)

    emprecp_bankaccount_name = (request.form.get('bank_account_name') or '').strip()
    emprecp_bank_number = (request.form.get('bank_account_number') or '').strip()
    emprecp_bank_code = (request.form.get('bank_code') or '').strip()

    if not emprecp_bankaccount_name or not emprecp_bank_number or not emprecp_bank_code:
        flash( "errormsg", "Please fill in all required fields.")
        return redirect(url_for('update_bankdetails'))

    if not emprecp_bank_number.isdigit() or len(emprecp_bank_number) != 10:
        flash("errormsg", "Account number must be 10 digits.")
        return redirect(url_for('update_bankdetails'))

    recipient = EmployerRecipient.query.filter_by(emprecp_employerid=loggedin_employer).first()

    if recipient:
        recipient.emprecp_bankaccount_name = emprecp_bankaccount_name
        recipient.emprecp_bank_number = emprecp_bank_number
        recipient.emprecp_bank_code = emprecp_bank_code
    else:
        recipient = EmployerRecipient(
            emprecp_employerid=loggedin_employer,
            emprecp_bankaccount_name = emprecp_bankaccount_name,
            emprecp_bank_number = emprecp_bank_number,
            emprecp_bank_code = emprecp_bank_code
        )
        db.session.add(recipient)

    try:
        db.session.commit()
        flash("success", "Bank details updated successfully.")
    except Exception:
        db.session.rollback()
        app.logger.exception("Updating employer bank details failed")
        flash("errormsg", "Error updating bank details. Please try again.")

    return redirect(url_for('employer_wallet'))





@app.route('/review/<int:post_id>', methods=['GET', 'POST'])
def review_worker(post_id):
    loggedin_employer = session.get('loggedin')
    if not loggedin_employer:
        flash("errormsg", "You must be logged in")
        return redirect(url_for('login'))
    employer_deets = db.session.query(Employer).get(loggedin_employer)
    # Retrieve the job posting.
    job = db.session.query(JobPosting).get(post_id)
    if not job or job.post_employerid != loggedin_employer:
        flash("errormsg", "Job not found.")
        return redirect(url_for('dashboard'))

    # Ensure that the job is completed.
    if job.post_status != "3":
        flash("errormsg", "You can only review completed jobs.")
        return redirect(url_for('dashboard'))

    if job.reviews:
        flash("errormsg", "You have already reviewed this job.")
        return redirect(url_for('dashboard'))

    if request.method == 'GET':
        return render_template('employer/review.html', job=job, employer_deets=employer_deets)
    else:
        # Process the review form submission.
        review_text = (request.form.get('review_text') or '').strip()
        try:
            rating = float(request.form.get('rating'))
        except (TypeError, ValueError):
            rating = None
        if not review_text or rating is None or not 1 <= rating <= 5:
            flash("errormsg", "Please give a rating from 1 to 5 and a comment.")
            return redirect(url_for('review_worker', post_id=post_id))

        new_review = Review(
            review_workerid=job.post_workerid,
            review_employerid=loggedin_employer,
            review_jobid=job.post_id,
            review_comment=review_text,
            review_rating=rating
        )
        db.session.add(new_review)
        db.session.commit()
        flash("success","Review submitted successfully!")
        return redirect(url_for('dashboard'))



@app.route('/logout/')
def logout():
    session.clear()
    flash('feedback', "You have logged out....")
    return redirect('/login/')
