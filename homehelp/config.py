import os

from dotenv import load_dotenv

load_dotenv()


def _env_bool(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in ('1', 'true', 'yes', 'on')


class BaseConfig(object):
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Recycle connections before MySQL's wait_timeout drops them
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True, 'pool_recycle': 280}

    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT') or 465)
    MAIL_USE_SSL = _env_bool('MAIL_USE_SSL')
    MAIL_USE_TLS = _env_bool('MAIL_USE_TLS')
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER') or os.getenv('MAIL_USERNAME')

    PAYSTACK_SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY')

    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'test@gmail.com')

    # Absolute path so saving works regardless of the working directory.
    # Templates serve these from /static/images/uploads/, so a persistent disk
    # in production should be mounted at this path.
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER') or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'static', 'images', 'uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB upload limit

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = _env_bool('SESSION_COOKIE_SECURE')

    # Number of reverse proxies in front of the app (Render/Railway/Nginx = 1)
    PROXY_COUNT = int(os.getenv('PROXY_COUNT') or 0)


REQUIRED_SETTINGS = ('SECRET_KEY', 'SQLALCHEMY_DATABASE_URI', 'PAYSTACK_SECRET_KEY')
