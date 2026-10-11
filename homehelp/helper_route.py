from flask import render_template,request,redirect,session,flash,url_for
from werkzeug.security import generate_password_hash, check_password_hash

from homehelp.models import db,Worker,Employer, Experience,Category,JobPosting,WorkerRecipient,Withdrawal
from homehelp.forms import HelpLoginForm, HelpSigninForm
from homehelp.utils import save_image, parse_amount
from homehelp import app
from decimal import Decimal


@app.route('/helper/register/', methods=["GET", "POST"])
def helper_register():
    helpsigninform = HelpSigninForm()
    helpsigninform.category.choices = [(0, 'Select a category')] + [
    (c.cat_id, c.cat_name) for c in Category.query.all()
]
    if request.method == 'GET':
        return render_template('helper/helper_registration.html', helpsigninform=helpsigninform)
    else:
        if helpsigninform.validate_on_submit():
            email = helpsigninform.email.data

            if helpsigninform.state.data == '0':
                flash('errormsg', 'Please select a valid state.')
                return render_template('helper/helper_registration.html', helpsigninform=helpsigninform)

            if helpsigninform.category.data == 0:
                flash( "errormsg", "Please select a category")
                return render_template("helper/helper_registration.html", helpsigninform=helpsigninform)

            price = parse_amount(helpsigninform.price.data)
            if price is None:
                flash("errormsg", "Please enter a valid price.")
                return render_template("helper/helper_registration.html", helpsigninform=helpsigninform)

            if Worker.query.filter_by(worker_email=email).first():
                flash("errormsg", "Already have an account, Please use a different email.")
                return redirect('/helper/register/')

            hashed_password = generate_password_hash(helpsigninform.password.data, method='pbkdf2:sha256')
            new_worker = Worker(
                worker_fname=helpsigninform.fname.data,
                worker_lname=helpsigninform.lname.data,
                worker_password=hashed_password,
                worker_email=email,
                worker_phoneno=helpsigninform.phone.data,
                worker_address=helpsigninform.address.data,
                worker_stateid=helpsigninform.state.data,
                worker_categoryid=helpsigninform.category.data,
                worker_price=price,
                worker_status='active'
            )

            db.session.add(new_worker)
            db.session.commit()

            worker_id = new_worker.worker_id
            # Only the person who just registered may fill in this worker's verification step
            session['pending_worker_id'] = worker_id

            flash('success', 'An account has been created for you!')
            return redirect(url_for('helper_verification', worker_id=worker_id))

        return render_template('helper/helper_registration.html', helpsigninform=helpsigninform)



@app.route('/helper/<int:worker_id>/verification/', methods=["GET","POST"])
def helper_verification(worker_id):
    if worker_id not in (session.get('pending_worker_id'), session.get('worker_id')):
        flash('errormsg', 'Please log in to continue.')
        return redirect(url_for('helper_login'))

    if request.method == 'GET':
        return render_template('helper/helper_verification.html',worker_id=worker_id)
    else:
        # retrieve form data
        years = request.form.get('exp_years')
        about = request.form.get('exp_about')
        if not years or not about:
            flash('errormsg', 'Please fill in your experience details.')
            return redirect(url_for('helper_verification', worker_id=worker_id))

        filename = save_image(request.files.get('exp_picture'))
        if not filename:
            flash('errormsg', 'Your cover image must be an image file')
            return redirect(url_for('helper_verification', worker_id=worker_id))
        # Save to database
        push = Experience(
            exp_years=years,
            exp_about=about,
            exp_picture=filename,
            exp_workerid=worker_id
        )
        db.session.add(push)
        db.session.commit()
        session.pop('pending_worker_id', None)

        flash('success','Profile created successfully')
        return redirect(url_for('helper_login'))




@app.route('/helper/login/',methods=["GET","POST"])
def helper_login():
    helploginform = HelpLoginForm()
    if request.method == "GET":
        return render_template('helper/helper_login.html', helploginform=helploginform)
    else:
        if helploginform.validate_on_submit():
            email = helploginform.email.data
            password = helploginform.password.data

            record = db.session.query(Worker).filter(Worker.worker_email==email).first()
            if not record or not check_password_hash(record.worker_password, password):
                flash('errormsg', 'Invalid email or password')
                return redirect('/helper/login/')
            if record.worker_status == "inactive":
                flash('errormsg', 'Your account is inactive. Please contact admin.')
                return redirect('/helper/login/')

            # Start a fresh session so no other role's login carries over
            session.clear()
            session['role'] = 'worker'
            session['worker_id'] = record.worker_id
            session['loggedin_worker'] = True
            return redirect('/helper/dashboard/')

        flash('errormsg', 'Invalid form submission, Please fill in all fields')
        return redirect('/helper/login/')



@app.route('/helper/dashboard/', methods=["GET"])
def helper_dashboard():
    loggedin_worker = session.get('worker_id')
    if loggedin_worker:
        worker_deets = db.session.query(Worker).get(loggedin_worker)
        experiences = worker_deets.experiences
        # Fetch assigned jobs
        assigned_jobs = db.session.query(JobPosting).filter_by(post_workerid=loggedin_worker).all()

        return render_template(
            'helper/helper_dashboard.html',
            worker_deets=worker_deets,
            assigned_jobs=assigned_jobs,
            experiences=experiences
        )
    else:
        flash('errormsg', 'You must be logged in.')
        return redirect('/helper/login/')



@app.route('/update/jobstatus/', methods=['POST'])
def update_jobstatus():
    loggedin_worker = session.get('worker_id')
    if not loggedin_worker:
        flash("errormsg","You must be logged in as a worker.")
        return redirect(url_for('helper_login'))

    try:
        post_id = int(request.form.get('post_id'))
    except (TypeError, ValueError):
        flash("errormsg", "Invalid job ID.")
        return redirect(url_for('helper_dashboard'))

    action = request.form.get('action')
    job = db.session.query(JobPosting).with_for_update().filter_by(post_id=post_id).first()
    # Workers can only respond to jobs that were sent to them
    if not job or job.post_workerid != loggedin_worker:
        db.session.rollback()
        flash("errormsg", "Job not found.")
        return redirect(url_for('helper_dashboard'))

    if job.post_status != '0':
        db.session.rollback()
        flash("errormsg", "You have already responded to this job.")
        return redirect(url_for('helper_dashboard'))

    if action == "1":
        job.post_status = '1'  # '1' means accepted
        flash("feedback", "Job accepted successfully!")
    elif action == "2":
        job.post_status = '2'  # '2' means rejected
        # Refund the employer the payment that funded this job, once
        payment = job.payment
        if payment and payment.pay_status == 'paid':
            employer = db.session.get(Employer, job.post_employerid, with_for_update=True)
            if employer:
                employer.employer_walletbalance = (employer.employer_walletbalance or Decimal('0')) + payment.pay_amount
                payment.pay_status = 'refunded'
        flash("feedback", "Job rejected.")
    else:
        db.session.rollback()
        flash("errormsg", "Invalid action.")
        return redirect(url_for('helper_dashboard'))

    db.session.commit()
    return redirect(url_for('helper_dashboard'))



@app.route('/worker/update_bank_details/', methods=['GET', 'POST'])
def update_bank_details():
    loggedin_worker = session.get('worker_id')
    if not loggedin_worker:
        flash("errormsg", "You must be logged in as an helper.")
        return redirect(url_for('helper_login'))

    if request.method == 'GET':
        worker_deets = db.session.query(Worker).get(loggedin_worker)
        recipient = db.session.query(WorkerRecipient).filter_by(recp_workerid=loggedin_worker).first()
        return render_template('helper/helper_payout.html',recipient=recipient,worker_deets=worker_deets)

    recp_bankaccount_name = (request.form.get('bank_account_name') or '').strip()
    recp_bank_number = (request.form.get('bank_account_number') or '').strip()
    recp_bank_code = (request.form.get('bank_code') or '').strip()

    if not recp_bankaccount_name or not recp_bank_number or not recp_bank_code:
        flash( "errormsg", "Please fill in all required fields.")
        return redirect(url_for('update_bank_details'))

    if not recp_bank_number.isdigit() or len(recp_bank_number) != 10:
        flash("errormsg", "Account number must be 10 digits.")
        return redirect(url_for('update_bank_details'))

    recipient = WorkerRecipient.query.filter_by(recp_workerid=loggedin_worker).first()

    if recipient:
        recipient.recp_bankaccount_name = recp_bankaccount_name
        recipient.recp_bank_number = recp_bank_number
        recipient.recp_bank_code = recp_bank_code
    else:
        recipient = WorkerRecipient(
            recp_workerid=loggedin_worker,
            recp_bankaccount_name = recp_bankaccount_name,
            recp_bank_number = recp_bank_number,
            recp_bank_code = recp_bank_code
        )
        db.session.add(recipient)

    try:
        db.session.commit()
        flash("success", "Bank details updated successfully.")
        return redirect (url_for('request_withdrawal'))
    except Exception:
        db.session.rollback()
        app.logger.exception("Updating worker bank details failed")
        flash("errormsg", "Error updating bank details. Please try again.")

    return redirect(url_for('helper_dashboard'))



@app.route('/helper/request_withdrawal/', methods=['GET', 'POST'])
def request_withdrawal():
    loggedin_worker = session.get('worker_id')
    if not loggedin_worker:
        flash("errormsg", "You must be logged in")
        return redirect(url_for('helper_login'))

    if request.method == 'GET':
        worker_deets = db.session.query(Worker).get(loggedin_worker)
        return render_template('helper/helper_withdrawal.html', worker_deets=worker_deets)

    amount = parse_amount(request.form.get('amount'))
    if amount is None:
        flash("errormsg", "Invalid withdrawal amount.")
        return redirect(url_for('request_withdrawal'))

    recipient = db.session.query(WorkerRecipient).filter_by(recp_workerid=loggedin_worker).first()
    if not recipient:
        flash("errormsg", "Please add your bank details first.")
        return redirect(url_for('update_bank_details'))

    # Lock the row so two simultaneous requests can't both spend the same balance
    worker_deets = db.session.get(Worker, loggedin_worker, with_for_update=True)
    balance = worker_deets.worker_walletbalance or Decimal('0')
    if amount > balance:
        db.session.rollback()
        flash("errormsg", "Insufficient funds.")
        return redirect(url_for('request_withdrawal'))

    worker_deets.worker_walletbalance = balance - amount

    new_withdrawal = Withdrawal(
        withdraw_userid=loggedin_worker,
        withdraw_usertype='worker',
        withdraw_amount=amount,
        withdraw_status='pending'
    )
    db.session.add(new_withdrawal)

    try:
        db.session.commit()
        flash("success", "Withdrawal request submitted. Your funds will be processed manually.")
        return redirect(url_for('request_withdrawal'))
    except Exception:
        db.session.rollback()
        app.logger.exception("Worker withdrawal failed")
        flash("errormsg", "Error processing withdrawal. Please try again.")

    return redirect(url_for('helper_dashboard'))



@app.route('/helper/profile/')
def helper_profile():
    loggedin_worker = session.get('worker_id')
    if loggedin_worker:
        worker_deets = db.session.query(Worker).get(loggedin_worker)
        state = worker_deets.state.state_name if worker_deets.state else "Not specified"
        experiences = worker_deets.experiences
        return render_template('helper/helper_profile.html', worker_deets=worker_deets,state=state,experiences=experiences)
    else:
        flash('errormsg', 'You must be loggedin')
        return redirect("/helper/login/")



@app.route('/update/<worker_id>/profile/',methods=["GET",'POST'])
def profile_update(worker_id):
    loggedin_worker = session.get('worker_id')
    if loggedin_worker:
        # Always edit the logged-in worker, never the id in the URL
        worker_deets = db.session.query(Worker).get(loggedin_worker)
        experiences = worker_deets.experiences
        if request.method == "POST":
            filename = save_image(request.files.get('exp_picture'))
            if filename is False:
                flash('errormsg', 'Your cover image must be an image file')
                return redirect('/helper/profile/')

            worker_price = request.form.get('price')
            if worker_price:
                price = parse_amount(worker_price)
                if price is None:
                    flash('errormsg', 'Please enter a valid price.')
                    return redirect('/helper/profile/')
                worker_deets.worker_price = price

            worker_deets.worker_fname = request.form.get('fname') or worker_deets.worker_fname
            worker_deets.worker_lname = request.form.get('lname') or worker_deets.worker_lname
            worker_deets.worker_phoneno = request.form.get('phone') or worker_deets.worker_phoneno
            worker_deets.worker_address = request.form.get('address') or worker_deets.worker_address
            if filename and experiences:
                experiences[0].exp_picture = filename
            db.session.commit()
            flash("feedback", "Profile details updated successfully!")
            return redirect('/helper/profile/')
        else:
            return redirect('/helper/profile/')
    else:
        flash('errormsg', 'You must be loggedin')
        return redirect("/helper/login/")



@app.route('/helper/logout/')
def helper_logout():
    session.clear()
    flash('feedback', "You have logged out....")
    return redirect('/helper/login/')
