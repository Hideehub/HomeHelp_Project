import os,secrets
from flask import render_template,request,redirect,session,flash,url_for
from werkzeug.security import generate_password_hash, check_password_hash

from homehelp.models import db,Worker,Employer, Experience,Category,JobPosting,WorkerRecipient,Withdrawal,Payment
from homehelp.forms import HelpLoginForm, HelpSigninForm
from homehelp import app
from decimal import Decimal


@app.route('/helper/register/', methods=["GET", "POST"])
def helper_register():
    helpsigninform = HelpSigninForm()
    helpsigninform.category.choices = [(cat.cat_id, cat.cat_name) for cat in db.session.query(Category).all()]
    if request.method == 'GET':
        return render_template('helper/helper_registration.html', helpsigninform=helpsigninform)
    else:
        print(request.form, helpsigninform.validate_on_submit())
        print(helpsigninform.errors)
        
        if helpsigninform.validate_on_submit():
            email = helpsigninform.email.data

            if helpsigninform.state.data == '0':
                flash('errormsg', 'Please select a valid state.')
                return render_template('helper/helper_registration.html', helpsigninform=helpsigninform)

            if Worker.query.filter_by(worker_email=email).first():
                flash("errormsg", "Already have an account, Please use a different email.")
                return redirect('/helper/register/')
            
            password = helpsigninform.password.data
            cpassword = helpsigninform.cpassword.data
            fname = helpsigninform.fname.data
            lname = helpsigninform.lname.data
            phone = helpsigninform.phone.data
            address = helpsigninform.address.data
            state = helpsigninform.state.data
            category = helpsigninform.category.data
            price = helpsigninform.price.data

            # Check if passwords match
            if password != cpassword:
                flash('Password mismatch, please ensure you enter the password correctly')
                return redirect('/helper/register/')
            else:
                hashed_password = generate_password_hash(password)
                new_worker = Worker(
                    worker_fname=fname,
                    worker_lname=lname,
                    worker_password=hashed_password,
                    worker_email=email,
                    worker_phoneno=phone,
                    worker_address=address,
                    worker_stateid=state,
                    worker_categoryid=category,
                    worker_price=price,
                    worker_status='active'
                )
                
                db.session.add(new_worker)
                db.session.commit()

                worker_id = new_worker.worker_id

                flash('success', 'An account has been created for you!')
                return redirect(url_for('helper_verification', worker_id=worker_id))

        return render_template('helper/helper_registration.html', helpsigninform=helpsigninform)



@app.route('/helper/<int:worker_id>/verification/', methods=["GET","POST"])
def helper_verification(worker_id):
    if request.method == 'GET':
        return render_template('helper/helper_verification.html',worker_id=worker_id)
    else:
    # retrieve form data
        years = request.form.get('exp_years')
        about = request.form.get('exp_about')

        # Retrieve file data 
        allowed_ext =['.jpg','.jpeg', '.png', '.gif']
        file = request.files.get('exp_picture')
        _,ext = os.path.splitext(file.filename)
        rand_str = secrets.token_hex(10)
        filename =''
        if ext in allowed_ext:
            filename = f'{rand_str}{ext}'
            file.save(f'homehelp/static/images/uploads/{filename}')
        else:
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

        flash('success','Profile created successfully')
        return redirect(url_for('helper_login', worker_id=worker_id))
       



@app.route('/helper/login/',methods=["GET","POST"])
def helper_login():
    helploginform = HelpLoginForm()
    if request.method == "GET":
        return render_template('helper/helper_login.html', helploginform=helploginform)
    else:
        if helploginform.validate_on_submit():
            if session.get('role') == 'employer':
                session.clear()

            email = helploginform.email.data
            password = helploginform.password.data
            
            record = db.session.query(Worker).filter(Worker.worker_email==email).first()
            if not record:
                flash('errormsg', 'Invalid Email')
                return redirect('/helper/login/')
            if record.worker_status == "inactive":
                flash('errormsg', 'Your account is inactive. Please contact admin.')
                return redirect('/helper/login/')
            hashed_password = record.worker_password
            chk = check_password_hash(hashed_password, password)
            if chk:
                session['role'] = 'worker'
                session['worker_id'] = record.worker_id
                session['loggedin_worker'] = True
                return redirect('/helper/dashboard/')
            else:
                flash('errormsg', 'Invalid Password')
                return redirect('/helper/login/')
     
     

@app.route('/helper/dashboard/', methods=["GET"])
def helper_dashboard():
    loggedin_worker = session.get('worker_id')
    print(loggedin_worker)
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
        flash("warning","You must be logged in as a worker.")
        return redirect(url_for('helper_login'))  

    post_id_str = request.form.get('post_id')
    try:
        post_id = int(post_id_str)
    except (TypeError, ValueError):
        flash("warning", "Invalid job ID.")
        return redirect(url_for('helper_dashboard')) 

    action = request.form.get('action')
    job = JobPosting.query.get(post_id)
    if not job:
        flash("warning", "Job not found.")
        return redirect(url_for('helper_dashboard'))

    if job.post_status in ['1', '2', '3']:
        flash("warning", "You have already responded to this job.")
        return redirect(url_for('helper_dashboard'))

    if action == "1":
        job.post_status = '1'  # '1' means accepted
        job.post_workerid = loggedin_worker
        flash("feedback", "Job accepted successfully!")
    elif action == "2":
        job.post_status = '2'  # '2' means rejected
        payment = Payment.query.filter(
            Payment.pay_employerid == job.post_employerid,
            Payment.pay_workerid == job.post_workerid,
            Payment.pay_status == 'paid'
        ).first()
        employer = Employer.query.get(job.post_employerid)
        if payment and employer:
            # Ensuring employer wallet_balance is initialized.
            if employer.employer_walletbalance is None:
                employer.employer_walletbalance = Decimal('0')
            employer.employer_walletbalance = employer.employer_walletbalance + payment.pay_amount
        flash("warning", "Job rejected.")
    elif action == "3":
        job.post_status = '3'  # '3' means job completed
        flash("feedback", "Job marked as completed.")
    else:
        flash("warning", "Invalid action.")
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

    recp_bankaccount_name = request.form.get('bank_account_name')
    recp_bank_number = request.form.get('bank_account_number')
    recp_bank_code = request.form.get('bank_code')

    if not recp_bankaccount_name or not recp_bank_number or not recp_bank_code:
        flash( "errormsg", "Please fill in all required fields.")
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
    except Exception as e:
        db.session.rollback()
        flash("errormsg", "Error updating bank details: " + str(e))
    
    return redirect(url_for('helper_dashboard'))  



@app.route('/helper/request_withdrawal/', methods=['GET', 'POST'])
def request_withdrawal():
    loggedin_worker = session.get('worker_id')
    if not loggedin_worker:
        flash("errormsg", "You must be logged in")
        return redirect(url_for('helper_login'))

    worker_deets = db.session.query(Worker).get(loggedin_worker)
    if request.method == 'GET':
        return render_template('helper/helper_withdrawal.html', worker_deets=worker_deets)
    
    try:
        amount = float(request.form.get('amount'))
    except ValueError:
        flash("errormsg", "Invalid withdrawal amount.")
        return redirect(url_for('request_withdrawal'))

    if amount > float(worker_deets.worker_walletbalance):
        flash("errormsg", "Insufficient funds.")
        return redirect(url_for('request_withdrawal'))

    recipient = db.session.query(WorkerRecipient).filter_by(recp_workerid=loggedin_worker).first()
    if not recipient:
        return redirect(url_for('update_bank_details'))

    worker_deets.worker_walletbalance = worker_deets.worker_walletbalance - Decimal(amount)

    new_withdrawal = Withdrawal(
        withdraw_userid=loggedin_worker,
        withdraw_usertype='worker',
        withdraw_amount=Decimal(amount),
        withdraw_status='pending'
    )
    db.session.add(new_withdrawal)

    try:
        db.session.commit()
        flash("success", "Withdrawal request submitted. Your funds will be processed manually.")
        return redirect(url_for('request_withdrawal'))
    except Exception as e:
        db.session.rollback()
        flash("errormsg", "Error processing withdrawal: " + str(e))
    
    return redirect(url_for('helper_dashboard'))



@app.route('/helper/profile/')
def helper_profile():
    loggedin_worker = session.get('worker_id')
    if loggedin_worker:
        worker_deets = db.session.query(Worker).get(loggedin_worker)
        state = worker_deets.state.state_name
        experiences = worker_deets.experiences 
        return render_template('helper/helper_profile.html', worker_deets=worker_deets,state=state,experiences=experiences)
    else:
        flash('errormsg', 'You must be loggedin')
        return redirect("/helper/login/")
 
    

@app.route('/update/<worker_id>/profile/',methods=["GET",'POST'])
def profile_update(worker_id):
    loggedin_worker = session.get('worker_id')
    if loggedin_worker:
        worker_deets = db.session.query(Worker).get(worker_id)
        experiences = worker_deets.experiences 
        if request.method == "POST":
            worker_fname = request.form.get('fname')
            worker_lname = request.form.get('lname')
            worker_phone = request.form.get('phone')
            worker_address = request.form.get('address')
            worker_price = request.form.get('price')

            allowed_ext =['.jpg','.jpeg', '.png', '.gif']
            file = request.files.get('exp_picture')
            _,ext = os.path.splitext(file.filename)
            rand_str = secrets.token_hex(10)
            filename =''
            if ext in allowed_ext:
                filename = f'{rand_str}{ext}'
                file.save(f'homehelp/static/images/uploads/{filename}')
            else:
                flash('errormsg', 'Your cover image must be an image file')
                return redirect('/helper/profile/')
            
            worker_deets.worker_fname = worker_fname
            worker_deets.worker_lname = worker_lname
            worker_deets.worker_phoneno = worker_phone
            worker_deets.worker_address = worker_address
            worker_deets.worker_price = worker_price
            if experiences:
                experiences[0].exp_picture = filename
            db.session.commit()
            flash("feedback", "Profile details updated succeddfully!")
            return redirect('/helper/profile/')
        else:
            return redirect('/helper/profile/')
    else:
        flash('errormsg', 'You must be loggedin')
        return redirect("/helper/login/")



@app.route('/helper/logout/')
def helper_logout():
    session.pop('worker_id', None)
    flash('feedback', "You have logged out....")
    return redirect('/helper/login/')
