from flask import render_template,request,session,flash,url_for,redirect

from homehelp import app
from homehelp.models import db,Category,Worker,State,Review,Employer



@app.route('/about/')
def about():
    return render_template('landingpage/about.html')

@app.route('/')
def index():
    loggedin_employer = session.get('loggedin')
    if loggedin_employer:
        employer_deets = db.session.query(Employer).get(loggedin_employer)
    else:
        employer_deets = None

    state = db.session.query(State).all()

    worker = db.session.query(Worker).limit(3).all()

    review = (
        db.session.query(Review)
        .join(Employer)
        .distinct(Review.review_employerid)
        .order_by(Review.review_id.desc()).limit(6).all()
    )

    worker_data = []
    for w in worker:
        worker_data.append({
            'worker': w,
            'category': w.category.cat_name if w.category else None 
        })

    # Pass data to the template
    return render_template('landingpage/index.html', worker_data=worker_data, state=state, review=review,employer_deets=employer_deets)



@app.route('/ajax/search/', methods=['POST']) 
def search():
    search_data = request.form.get('search')
    search_result = ''
    if search_data != '':
        search_filter = f'%{search_data}%'
        categories = Category.query.filter(Category.cat_name.like(search_filter)).all()
        search_result = ''
        for category in categories:
            search_result += f' <a href="/employer/dashboard/?category_id={category.cat_id}" style="text-decoration:none; color:black"> <span>{category.cat_name}</span></a><br>'
        return search_result
    else:
        return search_result


@app.route('/hire/now/')
def hire_now():
    loggedin_employer = session.get('loggedin')
    if loggedin_employer:
        return redirect('/employer/dashboard/')
    return redirect('/login/')
