from flask import render_template,request,redirect,flash,session,jsonify,url_for

from homehelp import app
from homehelp.models import db,Admin,Worker,Employer,Review,Payment,Withdrawal,EmployerRecipient,WorkerRecipient
from homehelp.forms import AdminLoginForm

from werkzeug.security import check_password_hash

@app.route('/admin/login/',methods=['GET','POST'])
def admin():
    adminloginform = AdminLoginForm()
    if request.method == 'GET':
        return render_template('admin/admin_login.html',adminloginform=adminloginform)
    else:
        if adminloginform.validate_on_submit():
            email = adminloginform.email.data
            password = adminloginform.password.data
            record = db.session.query(Admin).filter(Admin.admin_email==email).first()
            if record:
                hashed_password = record.admin_password
                chk = check_password_hash(hashed_password,password)
                if chk:
                    session['is_admin'] = record.admin_id
                    return redirect('/admin/dashboard/')
                else:
                    flash('errormsg', 'Invalid Password')
                    return redirect('/admin/login/')
            else:
                flash('errormsg', 'Invalid Email')
                return redirect('/admin/login/')
        else:
            return render_template('admin/admin_login.html', adminloginform=adminloginform)

    
@app.route('/admin/dashboard/', methods=['GET'])
def admin_dashboard():
    loggedin_admin = session.get('is_admin')
    # Check if logged in as admin
    if not loggedin_admin:
        flash('You must be logged in as an admin.')
        return redirect('/admin/login')

    admin= Admin.query.all()
    workers = Worker.query.all()
    employers = Employer.query.all()
    reviews = Review.query.all()
    total_employers = Employer.query.count()
    total_workers = Worker.query.count()
    active_employers = Employer.query.filter_by(employer_status='active').count()
    active_workers = Worker.query.filter_by(worker_status='active').count()
    total_active_users = active_employers + active_workers

    return render_template('admin/admin_dashboard.html', 
                           workers=workers, employers=employers, 
                           reviews=reviews, admin=admin, 
                           total_users=total_employers + total_workers,
                           total_active_users=total_active_users
                           )




@app.route('/admin/change-status/', methods=['POST'])
def change_status():
    try:
        loggedin_admin = session.get('is_admin')
        if loggedin_admin:
            # Debugging - Log request
            print("Request received:", request.json)

            data = request.get_json()
            if not data:
                return jsonify({"message": "No data provided"}), 400

            worker_id = data.get('worker_id')
            new_status = data.get('worker_status')

            if not worker_id or not new_status:
                return jsonify({"message": "Missing worker ID or status"}), 400

            # Debugging - Log parsed data
            print(f"Worker ID: {worker_id}, New Status: {new_status}")

            # Find the worker by ID
            worker = Worker.query.get(worker_id)
            if not worker:
                return jsonify({"message": "Worker not found"}), 404

            # Update the status
            worker.worker_status = new_status
            db.session.commit()

            # Debugging - Log successful update
            print(f"Worker {worker_id} status updated to {new_status}")

            return jsonify({
                "message": f"Worker status updated to {new_status}.",
                "new_status": new_status
            }), 200

    except Exception as e:
        # Debugging - Log error
        print("Error occurred:", str(e))
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500



@app.route('/admin/changestatus/', methods=['POST'])
def changestatus():
    try:
        loggedin_admin = session.get('is_admin')
        if loggedin_admin:
            print("Request received:", request.json)

            data = request.get_json()
            if not data:
                return jsonify({"message": "No data provided"}), 400

            employer_id = data.get('employer_id')
            new_status = data.get('employer_status')

            if not employer_id or not new_status:
                return jsonify({"message": "Missing worker ID or status"}), 400

            print(f"Worker ID: {employer_id}, New Status: {new_status}")

            employer = Employer.query.get(employer_id)
            if not employer:
                return jsonify({"message": "Worker not found"}), 404

            # Update status
            employer.employer_status = new_status
            db.session.commit()

            # Debugging - Log successful update
            print(f"Worker {employer_id} status updated to {new_status}")

            return jsonify({
                "message": f"Worker status updated to {new_status}.",
                "new_status": new_status
            }), 200

    except Exception as e:
        print("Error occurred:", str(e))
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500
    


@app.route('/admin/reviews/')
def admin_reviews():
    if not session.get('is_admin'):
        flash("errormsg", "You must be an admin to access this page.")
        return redirect(url_for('admin'))
    reviews = Review.query.all() 
    admin= Admin.query.all()
    total_employers = Employer.query.count()
    total_workers = Worker.query.count()
    active_employers = Employer.query.filter_by(employer_status='active').count()
    active_workers = Worker.query.filter_by(worker_status='active').count()
    total_active_users = active_employers + active_workers # Fetch all reviews
    return render_template('admin/admin_review.html', 
                           reviews=reviews, 
                           admin=admin,
                           total_users=total_employers + total_workers,
                           total_active_users=total_active_users
                           )



@app.route('/admin/reviews/delete/<int:review_id>', methods=['POST'])
def delete_review(review_id):
    if not session.get('is_admin'):
        flash("errormsg", "You must be an admin to access this page.")
        return redirect(url_for('admin'))
    review = Review.query.get_or_404(review_id)
    db.session.delete(review)
    db.session.commit()
    flash('success' 'Review deleted successfully')
    return redirect(url_for('admin_reviews'))




@app.route('/admin/withdrawals/')
def admin_withdrawals():
    if not session.get('is_admin'):
        flash("errormsg", "You must be an admin to access this page.")
        return redirect(url_for('admin'))
    
    withdrawals = Withdrawal.query.filter_by(withdraw_status='pending').order_by(Withdrawal.created_at.desc()).all()
    total_employers = Employer.query.count()
    total_workers = Worker.query.count()
    active_employers = Employer.query.filter_by(employer_status='active').count()
    active_workers = Worker.query.filter_by(worker_status='active').count()
    total_active_users = active_employers + active_workers # Fetch all reviews
    payout_map = {}
    for w in withdrawals:
        if w.withdraw_usertype == 'employer':
            payout = EmployerRecipient.query.filter_by(emprecp_employerid=w.withdraw_userid).first()
            payout_map[w.withdraw_userid] = payout
        elif w.withdraw_usertype == 'worker':
            payout = WorkerRecipient.query.filter_by(recp_workerid=w.withdraw_userid).first()
            payout_map[w.withdraw_userid] = payout
    
    return render_template('admin/admin_credit.html', withdrawals=withdrawals, payout_map=payout_map,total_users=total_employers + total_workers,total_active_users=total_active_users)



@app.route('/admin/process_withdrawal/<int:withdraw_id>', methods=['POST'])
def process_withdrawal(withdraw_id):
    if not session.get('is_admin'):
        flash("errormsg", "You must be an admin to access this page.")
        return redirect(url_for('admin'))
    
    withdrawal = Withdrawal.query.get(withdraw_id)
    if not withdrawal:
        flash("errormsg", "Withdrawal request not found.")
        return redirect(url_for('admin_withdrawals'))
    
    withdrawal.withdraw_status = 'credited'
    try:
        db.session.commit()
        flash("success", "Withdrawal marked as processed.")
    except Exception as e:
        db.session.rollback()
        flash("errormsg", "Error processing withdrawal: " + str(e))
    
    return redirect(url_for('admin_withdrawals'))



@app.route('/admin/payments/')
def admin_payments():
    if not session.get('is_admin'):
        flash("errormsg", "You must be an admin to view this page.")
        return redirect(url_for('admin'))
    
    workers = Worker.query.all()
    employers = Employer.query.all()
    payments = Payment.query.order_by(Payment.pay_id.desc()).all()
    total_employers = Employer.query.count()
    total_workers = Worker.query.count()
    active_employers = Employer.query.filter_by(employer_status='active').count()
    active_workers = Worker.query.filter_by(worker_status='active').count()
    total_active_users = active_employers + active_workers
    
    return render_template('admin/admin_payments.html', payments=payments, workers=workers,
                           total_users=total_employers + total_workers,
                           total_active_users=total_active_users,
                           employers=employers)




@app.route('/admin/logout/')
def admin_logout():
    session.pop('is_admin', None)
    flash('feedback', "You have logged out....")
    return redirect('/admin/login/')

