from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()


class Admin(db.Model):
    admin_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    admin_username = db.Column(db.String(100), nullable=False)
    admin_password = db.Column(db.String(200), nullable=False)
    admin_email = db.Column(db.String(255), nullable=False, unique=True)
    admin_logindate = db.Column(db.DateTime(), default=datetime.utcnow)

class State(db.Model):
    state_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    state_name = db.Column(db.String(100), nullable=False)

     # Relationship
    workers = db.relationship('Worker', back_populates='state')
    employer = db.relationship('Employer', back_populates='state')


class Employer(db.Model):
    employer_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employer_name = db.Column(db.String(100), nullable=False)
    employer_email = db.Column(db.String(255), nullable=False, unique=True)
    employer_password = db.Column(db.String(200), nullable=False)
    employer_address = db.Column(db.Text(), nullable=True)
    employer_gender = db.Column(db.String(45), nullable=True)
    employer_picture = db.Column(db.String(100), nullable=True)
    employer_phoneno = db.Column(db.String(100), nullable=True)
    employer_status = db.Column(db.String(10), default="active")
    date_registered = db.Column(db.DateTime(), default=datetime.utcnow)
    employer_walletbalance = db.Column(db.Numeric, default=0)

    employer_stateid = db.Column(db.Integer, db.ForeignKey('state.state_id'), nullable=True)

    # relationship
    state = db.relationship('State', back_populates='employer')
    payments = db.relationship("Payment", back_populates="employer", lazy=True)



class Worker(db.Model):
    worker_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    worker_fname = db.Column(db.String(100), nullable=False)
    worker_lname = db.Column(db.String(100), nullable=False)
    worker_email = db.Column(db.String(255), nullable=False, unique=True)
    worker_phoneno = db.Column(db.String(100), nullable=False)
    worker_password = db.Column(db.String(200), nullable=False)
    worker_status = db.Column(db.String(10), default="active")
    worker_registrationdate = db.Column(db.DateTime(), default=datetime.utcnow)
    worker_gender = db.Column(db.String(45), nullable=True)
    worker_picture = db.Column(db.String(100), nullable=True)
    worker_availability = db.Column(db.Enum('0','1'), nullable=False, server_default=('0'))
    worker_verification = db.Column(db.Enum('0','1'), nullable=False, server_default=('0'))
    worker_address = db.Column(db.Text(), nullable=True)
    worker_price = db.Column(db.Numeric(10,2), nullable=False, default=0.00)
    worker_walletbalance = db.Column(db.Numeric, default=0)

    worker_stateid = db.Column(db.Integer, db.ForeignKey('state.state_id'), nullable=True)
    worker_categoryid = db.Column(db.Integer, db.ForeignKey('category.cat_id'), nullable=True)

    # Relationship
    state = db.relationship('State', back_populates='workers')
    category = db.relationship('Category', back_populates='workers')



class Experience(db.Model):
    exp_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    exp_about =db.Column(db.Text(), nullable=False)
    exp_jobtitle = db.Column(db.String(50), nullable=True)
    exp_years = db.Column(db.String(50), nullable=False)
    exp_picture=db.Column(db.String(100), nullable=True)
    exp_workerid = db.Column(db.Integer, db.ForeignKey('worker.worker_id'),nullable=True)

    # Relationship
    worker = db.relationship('Worker', backref='experiences')


class Category(db.Model):
    cat_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cat_name = db.Column(db.String(100), nullable=False)

     # Relationship
    workers = db.relationship('Worker', back_populates='category', lazy=True)
    job_postings = db.relationship('JobPosting', back_populates='category', lazy=True)


class Review(db.Model):
    review_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    review_rating = db.Column(db.Float(), nullable=True)
    review_comment = db.Column(db.Text(), nullable=False)
    review_workerid = db.Column(db.Integer, db.ForeignKey('worker.worker_id'),nullable=True)
    review_employerid = db.Column(db.Integer, db.ForeignKey('employer.employer_id'),nullable=True)
    review_jobid = db.Column(db.Integer, db.ForeignKey('jobposting.post_id'), nullable=True)


    employer = db.relationship('Employer', backref='reviews')
    worker = db.relationship('Worker', backref='reviews_as_worker', lazy=True)
    job = db.relationship("JobPosting", back_populates="reviews")

class JobApplication(db.Model):
    __tablename__ ='jobapplication'
    app_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    app_status = db.Column(db.Enum('0','1'), nullable=False, server_default=('0'))
    app_dateapplied = db.Column(db.DateTime(), default=datetime.utcnow)
    app_agreedamount = db.Column(db.Numeric, nullable=False)

    app_workerid = db.Column(db.Integer, db.ForeignKey('worker.worker_id'),nullable=True)


class JobPosting(db.Model):
    __tablename__ = 'jobposting'
    post_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    post_title = db.Column(db.String(100), nullable=True)
    post_description = db.Column(db.Text(), nullable=False)
    post_payrate = db.Column(db.Numeric, nullable=True)
    post_dateadded = db.Column(db.DateTime(), nullable=True)
    post_closingdate = db.Column(db.DateTime(), nullable=True)
    post_status = db.Column(db.Enum('0','1','2','3','4'), nullable=False, server_default=('0'))
    post_categoryid = db.Column(db.Integer, db.ForeignKey('category.cat_id'),nullable=True)
    post_employerid = db.Column(db.Integer, db.ForeignKey('employer.employer_id'),nullable=True)
    post_workerid = db.Column(db.Integer, db.ForeignKey('worker.worker_id'), nullable=True)

    # relaionship
    category = db.relationship('Category', back_populates='job_postings')
    employer = db.relationship('Employer', backref='job_postings', lazy=True)
    worker = db.relationship('Worker', backref='job_postings', lazy=True)
    reviews = db.relationship("Review", back_populates="job", lazy=True)

class Payment(db.Model):
    pay_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pay_amount = db.Column(db.Numeric, nullable=False)
    pay_date = db.Column(db.DateTime(), nullable=True)
    pay_status= db.Column(db.Enum('pending','paid','failed','credited'), nullable=False, server_default=("pending"))
    pay_data = db.Column(db.Text(), nullable=True)    
    pay_ref = db.Column(db.String(100), nullable=True)
    pay_employerid = db.Column(db.Integer, db.ForeignKey('employer.employer_id'),nullable=True)
    pay_workerid =  db.Column(db.Integer, db.ForeignKey('worker.worker_id'),nullable=True)

    #relationship
    employer = db.relationship("Employer", back_populates="payments")


class WorkerRecipient(db.Model):
    __tablename__ = 'worker_recipient'
    recp_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    recp_workerid = db.Column(db.Integer, db.ForeignKey('worker.worker_id'), nullable=False, unique=True)
    recp_code = db.Column(db.String(100), nullable=True)
    recp_createdat = db.Column(db.DateTime, default=datetime.utcnow)
    recp_bankaccount_name = db.Column(db.String(100), nullable=False)
    recp_bank_number = db.Column(db.String(20), nullable=False)
    recp_bank_code = db.Column(db.String(10), nullable=False)

    worker = db.relationship("Worker", backref="worker_recipient", lazy=True)
   


class EmployerRecipient(db.Model):
    __tablename__ = 'employer_recipient'
    emprecp_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    emprecp_employerid = db.Column(db.Integer, db.ForeignKey('employer.employer_id'), nullable=False, unique=True)
    emprecp_code = db.Column(db.String(100), nullable=True)
    emprecp_createdat = db.Column(db.DateTime, default=datetime.utcnow)
    emprecp_bankaccount_name = db.Column(db.String(100), nullable=False)
    emprecp_bank_number = db.Column(db.String(20), nullable=False)
    emprecp_bank_code = db.Column(db.String(10), nullable=False)

    employer = db.relationship("Employer", backref="worker_recipients", lazy=True)


class Withdrawal(db.Model):
    withdraw_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    withdraw_userid = db.Column(db.Integer, nullable=False)          # Either employer or worker
    withdraw_usertype = db.Column(db.String(100), nullable=False)       # e.g., 'worker' or 'employer'
    withdraw_amount = db.Column(db.Numeric, nullable=False)
    withdraw_status = db.Column(db.String(50), nullable=False, default='pending')  # pending, processed, failed, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)








    



