import click
from werkzeug.security import generate_password_hash

from homehelp import app
from homehelp.forms import SigninForm
from homehelp.models import db, Admin, Category, State


@app.cli.command('seed-states')
def seed_states():
    """Insert the Nigerian states used by the signup forms (ids must match the form choices)."""
    choices = [c for c in SigninForm.state.kwargs['choices'] if c[0] != 0]
    added = 0
    for state_id, name in choices:
        if not db.session.get(State, state_id):
            db.session.add(State(state_id=state_id, state_name=name))
            added += 1
    db.session.commit()
    click.echo(f'Added {added} states.')


@app.cli.command('add-category')
@click.argument('names', nargs=-1, required=True)
def add_category(names):
    """Add one or more helper categories, e.g. flask add-category Cleaner Cook Driver"""
    for name in names:
        if not Category.query.filter_by(cat_name=name).first():
            db.session.add(Category(cat_name=name))
    db.session.commit()
    click.echo('Categories: ' + ', '.join(c.cat_name for c in Category.query.all()))


@app.cli.command('create-admin')
@click.option('--email', prompt=True)
@click.option('--username', prompt=True)
@click.password_option()
def create_admin(email, username, password):
    """Create an admin account."""
    if Admin.query.filter_by(admin_email=email).first():
        raise click.ClickException('An admin with that email already exists.')
    db.session.add(Admin(admin_email=email, admin_username=username,
                         admin_password=generate_password_hash(password, method='pbkdf2:sha256')))
    db.session.commit()
    click.echo(f'Admin {email} created.')
