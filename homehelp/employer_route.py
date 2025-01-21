import os,secrets
from flask import render_template,request,redirect,flash,session,url_for,jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message

from homehelp import app,mail
from homehelp.models import db,Employer,Category,State,Worker,Experience,Review,JobPosting
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
            email = request.form.get('email')
            password = request.form.get('password')
            #run a query
            record = db.session.query(Employer).filter(Employer.employer_email==email).first()
            if record.employer_status == "inactive":
                flash("errormsg","Your account is inactive. Please contact admin.")
                return redirect("/login/")
            if record:
                hashed_password = record.employer_password
                print(hashed_password)
                chk = check_password_hash(hashed_password,password)
                if chk:
                    session['loggedin'] = record.employer_id
                    return redirect('/employer/dashboard/')
                else:
                    flash('errormsg', 'Invalid Password')
                    return redirect('/login/')
            else:
                flash('errormsg', 'Invalid Email')
                return redirect('/login/')
        else:
            return render_template('employer/login.html', loginform=loginform)
    
        

@app.route('/signup/', methods=['POST', 'GET'])
def signup():
    signinform = SigninForm()
    if request.method == 'GET':
        return render_template('employer/signup.html', signinform=signinform)
    else:
        print(request.form,signinform.validate_on_submit())
        print(signinform.errors)
        if signinform.validate_on_submit():
            email = signinform.email.data
            password = signinform.password.data
            cpassword = signinform.cpassword.data
            name = signinform.name.data
            gender = signinform.gender.data
            phone = signinform.phone.data
            address = signinform.address.data
            state = signinform.state.data
            if password != cpassword:
                flash('errormsg', 'Password mismatch, please ensure you enter the password correctly')
                return redirect('/signup/')
            else:
                hashed_password = generate_password_hash(password)
                new_employer = Employer(
                    employer_name=name,
                    employer_password=hashed_password,
                    employer_email=email,
                    employer_phoneno=phone,
                    employer_gender=gender,
                    employer_address=address,
                    employer_stateid=state,
                    employer_status ='active'
                )
                db.session.add(new_employer)
                db.session.commit()
                flash( 'success','An account has been created for you!')
                return redirect('/login/')
        return render_template('employer/signup.html', signinform=signinform)
    

@app.route('/employer/dashboard/', methods=["POST", "GET"])
def dashboard():
    loggedin_employer = session.get('loggedin')
    loggedin_worker = session.get('worker_id')
    if loggedin_employer:
        employer_deets = db.session.query(Employer).get(loggedin_employer)
        worker_deets = db.session.query(Worker).get(loggedin_worker)
    
        
        # Get all workers
        worker_deets = db.session.query(Worker).all()

        # Prepare worker data with reviews and experiences
        worker_data = []
        for worker in worker_deets:
            worker_data.append({
                'worker': worker,
                'experiences': worker.experiences if worker.experiences else [], 
                'state': worker.state.state_name if worker.state else "Not specified",
                'category': worker.category.cat_name if worker.category else "Not specified",
                'reviews': worker.reviews_as_worker if worker.reviews_as_worker else [] 
            })
        return render_template(
            'employer/dashboard.html',
            employer_deets=employer_deets,
            worker_data=worker_data,
            worker_deets=worker_deets
        )
        
    else:
        flash('errormsg', 'You must be logged in.')
        return redirect("/login/")



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
            
            #Update the business details
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




@app.route('/send-job-description/', methods=['GET', 'POST'])
def send_job_description():
    worker_email = request.form.get('worker_email')
    worker_name = request.form.get('worker_name')
    post_description = request.form.get('job_description')
    employer_id = session.get('loggedin') 
    worker_id=request.form.get('worker_id')

    if not post_description:
        flash("errormsg", "Please provide a job description.")
        return redirect(url_for('dashboard'))

    # Find worker by email
    worker = db.session.query(Worker).filter_by(worker_email=worker_email).first()

    if not worker:
        flash("errormsg", "Worker not found.")
        return redirect(url_for('dashboard'))

    # Store the job in the database
    new_job = JobPosting(post_workerid=worker_id, post_employerid=employer_id, post_description=post_description)
    db.session.add(new_job)
    db.session.commit()

    # Send email notification
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

    
    mail.send(msg)
    flash("success", "Job description sent successfully!")


    return redirect(url_for('dashboard'))




@app.route('/logout/')
def logout():
    session.pop('loggedin', None)
    flash('feedback', "You have logged out....")
    return redirect('/login/')


@app.route('/review/', methods=['GET'])
def review():
    loggedin_employer = session.get('loggedin')
    if loggedin_employer:
        employer_deets = db.session.query(Employer).get(loggedin_employer)
        workers = Worker.query.all()
    return render_template('employer/review.html',employer_deets=employer_deets,workers=workers)



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

        # Create a new Review instance
        review = Review(
            review_comment=comment,
            review_employerid=employer_id,
            review_workerid=worker_id
        )

        # Add the review to the session and commit to the database
        db.session.add(review)
        db.session.commit()
        flash("Review submitted successfully!", 'success')
        return redirect(url_for('dashboard', worker_id=worker.worker_id))

    return render_template('submit_review.html', workers=workers)

