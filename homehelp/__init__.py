import os

from flask import Flask
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from werkzeug.middleware.proxy_fix import ProxyFix

from homehelp import config
from homehelp.models import db

csrf = CSRFProtect()
mail = Mail()


def create_app():
    import homehelp.models

    app = Flask(__name__, instance_relative_config=True)

    # All settings come from environment variables (see .env.example)
    app.config.from_object(config.BaseConfig)
    # Optional local overrides; instance/ is not committed
    app.config.from_pyfile("config.py", silent=True)

    missing = [k for k in config.REQUIRED_SETTINGS if not app.config.get(k)]
    if missing:
        raise RuntimeError(f"Missing required settings: {', '.join(missing)}. Set them in the environment or .env")

    if app.config['PROXY_COUNT']:
        n = app.config['PROXY_COUNT']
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=n, x_proto=n, x_host=n)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    Migrate(app, db)
    csrf.init_app(app)
    mail.init_app(app)
    with app.app_context():
        db.create_all()
    
    return app


app = create_app()

from homehelp import employer_route, admin_route, helper_route, landingpage_route
from homehelp import forms, commands


@app.before_request
def drop_deactivated_sessions():
    """Log out employers/workers that an admin has deactivated since they logged in."""
    from flask import session
    from homehelp.models import Employer, Worker
    if session.get('loggedin'):
        user = db.session.get(Employer, session['loggedin'])
        if not user or user.employer_status != 'active':
            session.clear()
    elif session.get('worker_id'):
        user = db.session.get(Worker, session['worker_id'])
        if not user or user.worker_status != 'active':
            session.clear()
