from flask import session
from datetime import timedelta


def isinit(func):
    def wraps(a, *args, **kwargs):
        if a._init:
            return func(a, *args, **kwargs)
        else:
            raise Exception('You must init your LoginHandler!')
    return wraps


class LoginHandler:

    __instance = None

    def __new__(cls):
        if LoginHandler.__instance is None:
            LoginHandler.__instance = object.__new__(cls)
        return LoginHandler.__instance

    def __init__(self):
        self._init = False
        self.user_callback = None

    def init(self, app):
        self._init = True
        self.app = app
        self.app.before_request(self.before)

    @isinit
    def login_handler(self, user, remember=False):
        if remember:
            session['remember'] = True
        session['secret_tok'] = self.app.config['SECRET_KEY']
        session['user_id'] = str(user.id)

    @isinit
    def before(self):
        if self.user_callback:
            if 'user_id' in session:
                if 'secret_tok' not in session :
                    raise Exception('error session')
                if session['secret_tok'] != self.app.config['SECRET_KEY']:
                    raise Exception('error session')
                if 'remember' in session and session['remember'] == True:
                    session.permanent = True
                    self.app.permanent_session_lifetime = timedelta(minutes=1)
                else:
                    session.permanent = False
                return self.user_callback(session['user_id'])
            else:
                return self.user_callback(None)

    def load_user(self, callback):
        self.user_callback = callback
        return self.user_callback

    def logout(self):
        print('logout')
        session.pop('user_id', None)
        session.pop('remember', None)
        session.pop('secret_tok', None)
        print(session)




