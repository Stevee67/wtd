import os
import secret_data

class Config(object):

    MONGODB_SETTINGS = {
                'db': secret_data.DB_NAME,
                'host': secret_data.DB_HOST,
                'port': secret_data.DB_PORT,
                'username': secret_data.DB_USERNAME,
                'password': secret_data.DB_PASSWORD}

    if os.environ.get('OPENSHIFT_REPO_DIR'):
        MONGODB_SETTINGS = {
            'db': 'whattodo',
            'host': os.environ.get('OPENSHIFT_MONGODB_DB_HOST'),
            'port': int(os.environ.get('OPENSHIFT_MONGODB_DB_PORT')),
            'username': 'admin',
            'password': '1LhWT8qiDlvg'}
    else:
        MONGODB_SETTINGS = {
            'db': secret_data.DB_NAME,
            'host': secret_data.DB_HOST,
            'port': secret_data.DB_PORT}

    # config for send message
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = '587'
    MAIL_PASS = secret_data.MAIL_PASS
    SENDER_ADDRESS = secret_data.SENDER_ADDRESS

    PORT = os.environ.get('OPENSHIFT_PYTHON_PORT') or 8888
    HOST = os.environ.get('OPENSHIFT_PYTHON_IP') or '0.0.0.0'

    DEBUG = False
    TESTING = False

    SECRET_KEY = secret_data.SECRET_KEY



class DevelopmentConfig(Config):
    DEBUG = True



