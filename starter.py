import os

from homehelp import app

if __name__ == '__main__':
    # Local development only; production runs through gunicorn (see Procfile)
    app.run(debug=os.getenv('FLASK_DEBUG') == '1')
