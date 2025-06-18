from flask import render_template,request,session,redirect

from homehelp import app
from homehelp.models import db,Category,Worker,State,Review,Employer



@app.route('/about/')
def about():
    return render_template('landingpage/about.html')

@app.route('/')
def index():
    loggedin_employer = session.get('loggedin')
    loggedin_worker = session.get('worker_id')
    if loggedin_employer:
        employer_deets = db.session.query(Employer).get(loggedin_employer)
    else:
        employer_deets = None

    if loggedin_worker:
        worker_deets= db.session.query(Worker).get(loggedin_worker)
    else:
        worker_deets = None

    workers = Worker.query.limit(3).all()
    
    reviews = (
        db.session.query(Review)
        .join(Employer)
        .distinct(Review.review_employerid)
        .order_by(Review.review_id.desc())
        .limit(6)
        .all()
    )
    
    states = State.query.all()
    
    return render_template('landingpage/index.html', employer_deets=employer_deets,worker_deets=worker_deets,workers=workers, states=states, reviews=reviews)



@app.route('/ajax/search/', methods=['POST']) 
def search():
    search_data = request.form.get('search')
    search_result = ''
    if search_data != '':
        search_filter = f'%{search_data}%'
        categories = Category.query.filter(Category.cat_name.like(search_filter)).all()
        search_result = ''
        for category in categories:
            search_result += f' <a href="/all/helpers/?category_id={category.cat_id}" style="text-decoration:none; color:black"> <span>{category.cat_name}</span></a><br>'
        return search_result
    else:
        return search_result



@app.route('/hire/now/')
def hire_now():
    loggedin_employer = session.get('loggedin')
    if loggedin_employer:
        return redirect('/all/helpers/')
    return redirect('/login/')
