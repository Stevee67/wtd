import os


class Config(object):

    MONGODB_SETTINGS = {
                'db': 'whattodo',
                'host': 'localhost',
                'port': 27017,
                'username': 'itisfun',
                'password': 'mayIknow'}

    if os.environ.get('OPENSHIFT_REPO_DIR'):
        MONGODB_SETTINGS = {
            'db': 'whattodo',
            'host': os.environ.get('OPENSHIFT_MONGODB_DB_HOST'),
            'port': int(os.environ.get('OPENSHIFT_MONGODB_DB_PORT')),
            'username': 'admin',
            'password': '1LhWT8qiDlvg'}
    else:
        MONGODB_SETTINGS = {
            'db': 'whattodo',
            'host': 'localhost',
            'port': 27017}

    DB_HOST = 'localhost'
    DB_PORT = 5432
    DB_USERNAME = 'itisfun'
    DB_PASSWORD = 'mayIknow'
    DB_NAME = 'whattodo'

    # config for send message
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = '587'
    MAIL_PASS = 'nokia675320'
    SENDER_ADDRESS = 'stopa6767@gmail.com'

    PORT = os.environ.get('OPENSHIFT_PYTHON_PORT') or 8888
    HOST = os.environ.get('OPENSHIFT_PYTHON_IP') or '0.0.0.0'

    DEBUG = False
    TESTING = False

    SECRET_KEY = 'ldKSpasaloww8sada7daw8dsa77weddz4zxc25sddf;jhghghfylak73hgv'


class DevelopmentConfig(Config):
    DEBUG = True



