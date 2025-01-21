import os,secrets
from flask import render_template,request,redirect,session,flash,url_for
from werkzeug.security import generate_password_hash, check_password_hash

from homehelp.models import db,Worker,State,Experience,Category,JobPosting,JobApplication
from homehelp.forms import HelpLoginForm, HelpSigninForm
from homehelp import app


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
            password = helpsigninform.password.data
            cpassword = helpsigninform.cpassword.data
            fname = helpsigninform.fname.data
            lname = helpsigninform.lname.data
            phone = helpsigninform.phone.data
            address = helpsigninform.address.data
            state = helpsigninform.state.data
            category = helpsigninform.category.data

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
                    worker_status='active'
                )
                
                db.session.add(new_worker)
                db.session.commit()

                # Get the worker id
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
            file.save(f'homehelp/static/uploads/{filename}')
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
            email = helploginform.email.data
            password = helploginform.password.data
            #run a query
            record = db.session.query(Worker).filter(Worker.worker_email==email).first()
            if record.worker_status == "inactive":
                flash("errormsg", "Your account is inactive. Please contact admin.")
                return redirect("/helper/login/")
            if record:
                hashed_password = record.worker_password
                chk = check_password_hash(hashed_password,password)
                if chk:
                    session['worker_id'] = record.worker_id
                    session['loggedin_worker'] = True
                    return redirect('/helper/dashboard/')
                else:
                    flash('errormsg', 'Invalid Password')
                    return redirect('/helper/login/')
            else:
                flash('errormsg', 'Invalid Email')
                return redirect('/helper/login/')
        else:
            return render_template('helper/helper_login.html', helploginform=helploginform)
     
     

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
            # Retrieve from data
            worker_fname = request.form.get('fname')
            worker_lname = request.form.get('lname')
            worker_phone = request.form.get('phone')
            worker_address = request.form.get('address')

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
                return redirect('/helper/profile/')
            
            #Update the business details
            worker_deets.worker_fname = worker_fname
            worker_deets.worker_lname = worker_lname
            worker_deets.employer_phoneno = worker_phone
            worker_deets.employer_address = worker_address
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
    session.pop('loggedin', None)
    flash('feedback', "You have logged out....")
    return redirect('/helper/login/')
