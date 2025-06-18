from flask import Flask
#from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail

from homehelp import config
from homehelp.models import db 

csrf = CSRFProtect()
mail = Mail()

def create_app():
    from homehelp import models

    app = Flask(__name__,instance_relative_config=True)

    #to load all the config inside the file
    # app.config.from_pyfile("config.py")
    app.config.from_object(config.BaseConfig)

    #db = SQLAlchemy(app)
    db.init_app(app)
    migrate = Migrate(app,db)
    csrf.init_app(app)
    mail.init_app(app)

    return app
    
app = create_app()

from homehelp import employer_route, admin_route, helper_route,landingpage_route
from homehelp import forms

