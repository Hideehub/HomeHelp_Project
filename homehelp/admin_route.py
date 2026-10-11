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
            if record and check_password_hash(record.admin_password, password):
                session.clear()
                session['is_admin'] = record.admin_id
                return redirect('/admin/dashboard/')
            flash('errormsg', 'Invalid email or password')
            return redirect('/admin/login/')
        else:
            return render_template('admin/admin_login.html', adminloginform=adminloginform)

    
@app.route('/admin/dashboard/', methods=['GET'])
def admin_dashboard():
    loggedin_admin = session.get('is_admin')
    # Check if logged in as admin
    if not loggedin_admin:
        flash('errormsg', 'You must be logged in as an admin.')
        return redirect('/admin/login/')

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
    if not session.get('is_admin'):
        return jsonify({"message": "Admin login required"}), 403

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"message": "No data provided"}), 400

    record_id = data.get('worker_id')
    new_status = data.get('worker_status')

    if not record_id or new_status not in ('active', 'inactive'):
        return jsonify({"message": "Missing worker ID or invalid status"}), 400

    record = Worker.query.get(record_id)
    if not record:
        return jsonify({"message": "Worker not found"}), 404

    record.worker_status = new_status
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        app.logger.exception("Changing worker status failed")
        return jsonify({"message": "An error occurred, please try again."}), 500

    return jsonify({
        "message": f"Worker status updated to {new_status}.",
        "new_status": new_status
    }), 200



@app.route('/admin/changestatus/', methods=['POST'])
def changestatus():
    if not session.get('is_admin'):
        return jsonify({"message": "Admin login required"}), 403

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"message": "No data provided"}), 400

    record_id = data.get('employer_id')
    new_status = data.get('employer_status')

    if not record_id or new_status not in ('active', 'inactive'):
        return jsonify({"message": "Missing employer ID or invalid status"}), 400

    record = Employer.query.get(record_id)
    if not record:
        return jsonify({"message": "Employer not found"}), 404

    record.employer_status = new_status
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        app.logger.exception("Changing employer status failed")
        return jsonify({"message": "An error occurred, please try again."}), 500

    return jsonify({
        "message": f"Employer status updated to {new_status}.",
        "new_status": new_status
    }), 200



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
    flash('success', 'Review deleted successfully')
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
    if not withdrawal or withdrawal.withdraw_status != 'pending':
        flash("errormsg", "Pending withdrawal request not found.")
        return redirect(url_for('admin_withdrawals'))
    
    withdrawal.withdraw_status = 'credited'
    try:
        db.session.commit()
        flash("success", "Withdrawal marked as processed.")
    except Exception:
        db.session.rollback()
        app.logger.exception("Processing withdrawal failed")
        flash("errormsg", "Error processing withdrawal. Please try again.")
    
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
    session.clear()
    flash('feedback', "You have logged out....")
    return redirect('/admin/login/')

