from flask import render_template,request,redirect,flash,session,jsonify

from homehelp import app
from homehelp.models import db,Admin,Worker,Employer,Review
from homehelp.forms import AdminLoginForm

from werkzeug.security import generate_password_hash, check_password_hash

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
                    session['loggedin'] = record.admin_id
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
    loggedin_admin = session.get('loggedin')
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


@app.route('/admin/reviews/')
def admin_review():
    loggedin_admin = session.get('loggedin')
    if loggedin_admin:
        admin= Admin.query.all()
        reviews = Review.query.all()
        total_employers = Employer.query.count()
        total_workers = Worker.query.count()
        active_employers = Employer.query.filter_by(employer_status='active').count()
        active_workers = Worker.query.filter_by(worker_status='active').count()
        total_active_users = active_employers + active_workers
        return render_template('admin/admin_review.html', reviews=reviews, admin=admin,total_users=total_employers + total_workers,total_active_users=total_active_users)
    

@app.route('/admin/change-status/', methods=['POST'])
def change_status():
    try:
        loggedin_admin = session.get('loggedin')
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
        loggedin_admin = session.get('loggedin')
        if loggedin_admin:
            # Debugging - Log request
            print("Request received:", request.json)

            data = request.get_json()
            if not data:
                return jsonify({"message": "No data provided"}), 400

            employer_id = data.get('employer_id')
            new_status = data.get('employer_status')

            if not employer_id or not new_status:
                return jsonify({"message": "Missing worker ID or status"}), 400

            # Debugging - Log parsed data
            print(f"Worker ID: {employer_id}, New Status: {new_status}")

            # Find the worker by ID
            employer = Employer.query.get(employer_id)
            if not employer:
                return jsonify({"message": "Worker not found"}), 404

            # Update the status
            employer.employer_status = new_status
            db.session.commit()

            # Debugging - Log successful update
            print(f"Worker {employer_id} status updated to {new_status}")

            return jsonify({
                "message": f"Worker status updated to {new_status}.",
                "new_status": new_status
            }), 200

    except Exception as e:
        # Debugging - Log error
        print("Error occurred:", str(e))
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500
    

@app.route('/admin/manage-reviews/', methods=['GET'])
def manage_reviews():
    if not session.get('loggedin'):
        flash('errormsg', 'You must be logged in ')
        return redirect('/admin/login/')

    # Fetch all reviews along with worker and employer details
    reviews = Review.query.join(Worker).join(Employer).all()

    # Prepare data for the template
    review_data = [
        {
            'id': review.review_id,
            'worker_name': f"{review.worker.worker_fname} {review.worker.worker_lname}",
            'employer_name': review.employer.employer_name,
            'comment': review.review_comment,
        }
        for review in reviews
    ]

    return render_template('admin/manage_reviews.html', reviews=review_data)


@app.route('/admin/delete-review/<int:review_id>', methods=['POST'])
def delete_review(review_id):
    if not session.get('loggedin'):
        return jsonify({'message': 'Unauthorized access'}), 403

    # Fetch and delete the review
    review = Review.query.get_or_404(review_id)
    db.session.delete(review)
    db.session.commit()

    return jsonify({'message': 'Review deleted successfully!'}), 200


