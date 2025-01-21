class BaseConfig(object):
    ADMIN_EMAIL='test@email.com'

class LiveConfig(BaseConfig):
    SITE_ADDRESS='https://site.com'

class TestConfig(BaseConfig):
    SITE_ADDRESS='https://testsite.com'