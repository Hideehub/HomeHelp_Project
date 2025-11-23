import os,secrets,random,requests,json
from flask import render_template,request,redirect,flash,session,url_for,jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message
from decimal import Decimal

from homehelp import app,mail
from homehelp.models import db,Employer,Withdrawal,Worker,EmployerRecipient,Review,JobPosting,Payment
from homehelp.forms import LoginForm,SigninForm



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
            if session.get('role') == 'worker':
                session.clear()

            email = request.form.get('email')
            password = request.form.get('password')
        
            record = db.session.query(Employer).filter(Employer.employer_email == email).first()
            if not record:
                flash('errormsg', 'Invalid Email')
                return redirect('/login/')
                
            if record.employer_status == "inactive":
                flash('errormsg', 'Your account is inactive. Please contact admin.')
                return redirect('/login/')

            hashed_password = record.employer_password
            chk = check_password_hash(hashed_password, password)
            if chk:
                session['role'] = 'employer'
                session['loggedin'] = record.employer_id
                return redirect('/all/helpers/')
            else:
                flash('errormsg', 'Invalid Password')
                return redirect('/login/')

    
        

@app.route('/signup/', methods=['POST', 'GET'])
def signup():
    signinform = SigninForm()
    if request.method == 'GET':
        return render_template('employer/signup.html', signinform=signinform)
    
    if signinform.validate_on_submit():
        if signinform.state.data == '0':
            flash('errormsg', 'Please select a valid state.')
            return render_template('employer/signup.html', signinform=signinform)
        
        if signinform.password.data != signinform.cpassword.data:
            flash('errormsg','Password mismatch, please ensure you enter the password correctly')
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
        except Exception as e:
            db.session.rollback()
            flash('errormsg', 'An error occurred while creating your account. Please try again.')
            print("SIGNUP ERROR:", e)
            return render_template('employer/signup.html', signinform=signinform)
        
        flash('success', 'An account has been created for you!')
        return redirect('/login/')
    
    for field, errors in signinform.errors.items():
        for error in errors:
            flash(f"Error in {getattr(signinform, field).label.text}: {error}", 'errormsg')
    return render_template('employer/signup.html', signinform=signinform)

    

@app.route('/all/helpers/', methods=["POST", "GET"])
def helpers():
    loggedin_employer = session.get('loggedin')
    loggedin_worker = session.get('worker_id')
    if loggedin_employer:
        employer_deets = db.session.query(Employer).get(loggedin_employer)
        worker_deets = db.session.query(Worker).get(loggedin_worker)
    
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
        flash('warning', "You must be logged in")
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
        employer_deets = db.session.query(Employer).get(employer_id)

        if request.method == "POST":
            # Retrieve from data
            employer_name = request.form.get('name')
            employer_phone = request.form.get('phone')
            employer_address = request.form.get('address')

            # Retrieve file data 
            allowed_ext =['.jpg','.jpeg', '.png', '.gif']
            file = request.files.get('employer_picture')
            _,ext = os.path.splitext(file.filename)
            rand_str = secrets.token_hex(10)
            filename =''
            if ext in allowed_ext:
                filename = f'{rand_str}{ext}'
                file.save(f'homehelp/static/images/uploads/{filename}')
            else:
                flash('errormsg', 'Your cover image must be an image file')
                return redirect('/employer/profile/')
            
            employer_deets.employer_name = employer_name
            employer_deets.employer_phoneno = employer_phone
            employer_deets.employer_address = employer_address
            employer_deets.employer_picture = filename
            db.session.commit()
            flash("feedback", "Profile details updated succeddfully!")
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
        flash("You must be logged in", "errormsg")
        return redirect('/login/')
    
    worker = db.session.query(Worker).get(worker_id)
    if not worker:
        flash("errormsg", "Worker not found.")
        return redirect('/employer/dashboard/')
    
    if request.method == 'GET':
        employer_deets = db.session.query(Employer).get(loggedin_employer)
        session['worker_id'] = worker_id
        return render_template('employer/payment.html',
                               employer_deets=employer_deets,
                               worker=worker)
    else:
        amt = worker.worker_price
        ref = int(random.random() * 10000000000)
        session['refno'] = ref
        pay = Payment(pay_employerid=loggedin_employer, pay_amount=amt, pay_ref=ref, pay_workerid=worker_id)
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
    payment_deets = db.session.query(Payment).filter(Payment.pay_employerid == loggedin_employer).order_by(Payment.pay_id.desc()).first()
    refno = session.get('refno')
    if not refno:
        flash("errormsg", "Please start transaction from here")
        return redirect(url_for('make_payment', worker_id=worker_id))
    
    trxdeets = db.session.query(Payment).filter(Payment.pay_ref == refno).first()
    if not trxdeets:
        flash("errormsg", "Transaction details not found." )
        return redirect(url_for('make_payment', worker_id=worker_id))
    
    if request.method == 'GET':
        return render_template('employer/payment_confirm.html',
                               payment_deets=payment_deets,
                               trxdeets=trxdeets,
                               employer_deets=employer_deets,
                               worker=db.session.query(Worker).get(worker_id))
    else:
        # POST: Connect to Paystack to initialize the transaction.
        url = 'https://api.paystack.co/transaction/initialize'
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer sk_test_512e2c4255ce706a7084ae1449790ff3b086d7f5"
        }
        amt_kobo = float(trxdeets.pay_amount) * 100  # Convert to kobo.
        data = {
            "reference": refno,
            "amount": amt_kobo,
            "email": trxdeets.employer.employer_email,
            "callback_url": "http://127.0.0.1:5000/payment/update/" 
        }
        response = requests.post(url, headers=headers, data=json.dumps(data))
        json_response = response.json()
        if json_response.get("status"):
            authurl = json_response['data']['authorization_url']
            return redirect(authurl)
        else:
            flash("errormsg", json_response.get("message", "Error connecting to payment gateway"))
            return redirect(url_for('make_payment', worker_id=worker_id))




@app.route('/payment/update/', methods=['GET'])
def paystack_update():
    loggedin_employer = session.get('loggedin')
    refno = session.get('refno')
    if not loggedin_employer or not refno:
        flash("errormsg", "Transaction could not be verified.")
        worker_id = session.get('worker_id', 0)
        return redirect(url_for('make_payment', worker_id=worker_id))
    
    try:
        url = 'https://api.paystack.co/transaction/verify/' + str(refno)
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer sk_test_512e2c4255ce706a7084ae1449790ff3b086d7f5"
        }
        response = requests.get(url, headers=headers)
        rsp = response.json()
        status = rsp.get('status')
        pay = db.session.query(Payment).filter(Payment.pay_ref == refno).first()
        if status and rsp.get('data'):
            paystatus = rsp['data'].get('gateway_response', 'No response provided')
            pay.pay_status = 'paid'
            pay.pay_data = paystatus
            db.session.commit()
            # Retrieve worker_id from the payment record.
            worker_id = pay.pay_workerid
            # After a successful payment, redirect to the job description form.
            return redirect(url_for('job_description_form', worker_id=worker_id))
        else:
            paystatus = rsp.get('message', 'Payment failed')
            pay.pay_status = 'failed'
            pay.pay_data = paystatus
            db.session.commit()
            # Retrieve worker_id from session to redirect back to payment.
            worker_id = session.get('worker_id', 0)
            flash("errormsg", "Payment verification failed: " + paystatus)
            return redirect(url_for('make_payment', worker_id=worker_id))
    except Exception as e:
        worker_id = session.get('worker_id', 0)
        flash("errormsg", "Paystack is down, try again. Error: " + str(e))
        return redirect(url_for('make_payment', worker_id=worker_id))



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
    return render_template('employer/job_description.html',
                           employer_deets=employer_deets,
                           worker=worker)



@app.route('/send-job-description/', methods=['GET', 'POST'])
def send_job_description():
    worker_email = request.form.get('worker_email')
    worker_name = request.form.get('worker_name')
    category_id = request.form.get('worker_cat')
    category_name = request.form.get('worker_catname')
    post_description = request.form.get('job_description')
    employer_id = session.get('loggedin')
    worker_id = request.form.get('worker_id')

    if not post_description:
        flash("errormsg", "Please provide a job description.")
        return redirect(url_for('helpers'))

    worker = db.session.query(Worker).filter_by(worker_email=worker_email).first()
    if not worker:
        flash("errormsg","Worker not found.")
        return redirect(url_for('helpers'))

    try:
        new_job = JobPosting(
            post_workerid=worker_id, 
            post_employerid=employer_id, 
            post_description=post_description,
            post_categoryid=category_id,
            post_title=category_name
        )
        db.session.add(new_job)
        db.session.commit()
    except Exception as e:
        db.session.rollback()  
        flash("errormsg", "An error occurred while saving the job description: " + str(e))
        return redirect(url_for('helpers'))

    subject = "New Job Opportunity from HomeHelp"
    body = f"""
    Hello {worker_name},

    You have received a new job description:

    {post_description}

    Please log in to your account for more details.

    Best regards,
    HomeHelp Team
    """
    msg = Message(subject, sender='adeyemiidowu@moatcohorts.com.ng', recipients=[worker_email])
    msg.body = body
    try:
        mail.send(msg)
    except Exception as e:
        flash("errormsg", "Failed to send email notification: " + str(e))
        return redirect(url_for('helpers'))

    flash( "success", "Job description sent successfully!")
    return redirect(url_for('helpers'))



@app.route('/job/cancel/<int:post_id>', methods=['POST'])
def cancel_job(post_id):
    loggedin_employer = session.get('loggedin')
    if not loggedin_employer:
        flash("errormsg", "You must be logged in")
        return redirect(url_for('login'))

    job = db.session.query(JobPosting).get(post_id)
    if not job:
        flash("errormsg", "Job not found")
        return redirect(url_for('dashboard'))

    if job.post_employerid != loggedin_employer:
        flash("errormsg", "You are not authorized to cancel this job")
        return redirect(url_for('dashboard'))

    if job.post_status not in ['0', '1']:
        flash("errormsg", "Job cannot be cancelled at this stage")
        return redirect(url_for('dashboard'))

    job.post_status = '4'
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash("errormsg", "Error updating job status: " + str(e))
        return redirect(url_for('dashboard'))

    payment = db.session.query(Payment).filter(
        Payment.pay_employerid == loggedin_employer,
        Payment.pay_workerid == job.post_workerid,
        Payment.pay_status.in_(['pending', 'paid', 'failed','credited'])
    ).order_by(Payment.pay_id.desc()).first()

    if not payment:
        flash("errormsg", "No payment record found for this job.")
        return redirect(url_for('dashboard'))

    employer = db.session.query(Employer).get(loggedin_employer)
    if employer:
        if employer.employer_walletbalance is None:
            employer.employer_walletbalance = Decimal('0')
        employer.employer_walletbalance = employer.employer_walletbalance + payment.pay_amount

    payment.pay_status = 'refunded'
    try:
        db.session.commit()
        flash("success", "Job cancelled and payment refunded to your wallet for manual withdrawal.")
    except Exception as e:
        db.session.rollback()
        flash("errormsg", "Error processing refund: " + str(e))

    return redirect(url_for('dashboard'))




@app.route('/job/complete/<int:post_id>', methods=['POST'])
def complete_job(post_id):
    loggedin_employer = session.get('loggedin')
    if not loggedin_employer:
        flash("errormsg", "You must be logged in")
        return redirect(url_for('login'))

    job = db.session.query(JobPosting).get(post_id)
    if not job:
        flash("errormsg", "Job not found")
        return redirect(url_for('dashboard'))

    # Ensure the logged-in employer owns the job.
    if job.post_employerid != loggedin_employer:
        flash("errormsg", "You are not authorized to complete this job.")
        return redirect(url_for('dashboard'))

    job.post_status = "3"  
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash("errormsg", "Error updating job status: " + str(e))
        return redirect(url_for('dashboard'))
    
    payment = db.session.query(Payment).filter(
        Payment.pay_employerid == loggedin_employer,
        Payment.pay_workerid == job.post_workerid,
        Payment.pay_status == 'paid'  # Payment already received from employer.
    ).order_by(Payment.pay_id.desc()).first()
    
    if not payment:
        flash("errormsg", "No payment record found for this job.")
        return redirect(url_for('dashboard'))
    
    # Retrieve the worker's record.
    worker = db.session.query(Worker).get(job.post_workerid)
    if not worker:
        flash("errormsg", "Worker not found.")
        return redirect(url_for('dashboard'))
    
    try:
        worker.worker_walletbalance = worker.worker_walletbalance + payment.pay_amount
        payment.pay_status = 'credited'
        db.session.commit()
        flash("success", "Job completed and payout initiated. The funds have been added to the worker's wallet.")
    except Exception as e:
        db.session.rollback()
        flash("errormsg", "Error crediting worker: " + str(e))
    
    return redirect(url_for('dashboard'))



@app.route('/employer/wallet/', methods=['GET', 'POST'])
def employer_wallet():
    loggedin_employer = session.get('loggedin')
    if not loggedin_employer:
        flash("errormsg", "You must be logged in")
        return redirect(url_for('login'))
    employer_deets = db.session.query(Employer).get(loggedin_employer)
    if request.method == 'GET':
        return render_template('employer/employer_wallet.html', employer_deets=employer_deets)
    
    try:
        amount = float(request.form.get('amount'))
    except ValueError:
        flash("errormsg", "Invalid withdrawal amount.")
        return redirect(url_for('employer_wallet'))

    if amount > float(employer_deets.employer_walletbalance):
        flash("errormsg", "Insufficient funds.")
        return redirect(url_for('employer_wallet'))
    
    recipient = db.session.query(EmployerRecipient).filter_by(emprecp_employerid=loggedin_employer).first()
    if not recipient:
        return redirect(url_for('update_bankdetails'))

    employer_deets.employer_walletbalance = employer_deets.employer_walletbalance - Decimal(amount)

    new_withdrawal = Withdrawal(
        withdraw_userid=loggedin_employer,
        withdraw_usertype='employer',
        withdraw_amount=Decimal(amount),
        withdraw_status='pending'
    )
    db.session.add(new_withdrawal)

    try:
        db.session.commit()
        flash("success", "Withdrawal request submitted. Your funds will be processed manually.")
        return redirect(url_for('employer_wallet'))
    except Exception as e:
        db.session.rollback()
        flash("errormsg", "Error processing withdrawal: " + str(e))
    
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

    emprecp_bankaccount_name = request.form.get('bank_account_name')
    emprecp_bank_number = request.form.get('bank_account_number')
    emprecp_bank_code = request.form.get('bank_code')

    if not emprecp_bankaccount_name or not emprecp_bank_number or not emprecp_bank_code:
        flash( "errormsg", "Please fill in all required fields.")
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
    except Exception as e:
        db.session.rollback()
        flash("errormsg", "Error updating bank details: " + str(e))
    
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
    if not job:
        flash("errormsg", "Job not found.")
        return redirect(url_for('dashboard'))

    # Ensure that the job is completed.
    if job.post_status != "3":
        flash("errormsg", "You can only review completed jobs.")
        return redirect(url_for('dashboard'))

    if request.method == 'GET':
        return render_template('employer/review.html', job=job, employer_deets=employer_deets)
    else:
        # Process the review form submission.
        review_text = request.form.get('review_text')
        rating = request.form.get('rating')
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



@app.route('/submit_review/', methods=['GET', 'POST'])
def submit_review():
    loggedin_employer = session.get('loggedin')
    if not loggedin_employer:
             flash("errormsg", "Only employers can submit reviews")
             return redirect('/login/')

    workers = Worker.query.all()

    if request.method == 'POST':
        worker_id = request.form.get('worker_id')
        comment = request.form.get('comment')
        employer_id = loggedin_employer 

        worker = Worker.query.get(worker_id)
        if not worker:
            flash("errormsg", "The selected worker does not exist.")
            return redirect(url_for('submit_review'))

        review = Review(
            review_comment=comment,
            review_employerid=employer_id,
            review_workerid=worker_id
        )

        db.session.add(review)
        db.session.commit()
        flash("Review submitted successfully!", 'success')
        return redirect(url_for('helpers', worker_id=worker.worker_id))

    return render_template('submit_review.html', workers=workers)



@app.route('/logout/')
def logout():
    session.pop('loggedin', None)
    flash('feedback', "You have logged out....")
    return redirect('/login/')
