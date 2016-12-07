from flask import g, abort, session, request, redirect
import requests
from urllib.parse import urlparse, parse_qs
import os


class OpenId:
    __instance = None

    secret_key = None

    def __new__(cls, val):
        if OpenId.__instance is None:
            OpenId.__instance = object.__new__(cls)
            OpenId.__instance.val = val
        return OpenId.__instance

    @staticmethod
    def try_login(open_id, get_fields=None):
        OpenId.secret_key = str(os.urandom(28))
        url = open_id
        if'http' not in open_id:
            url = 'http://'+open_id
        fields = ''
        if get_fields:
            if not isinstance(get_fields, list):
                raise Exception('`get_fields` param must be list!')
            for field in get_fields:
                fields = fields+str(field)+';'
            fields = fields[0:-1]
        if len(fields) > 0:
            res = url+'/'+request.host+'?bod='+OpenId.secret_key+'&fields='+fields
        else:
            res = url+'/'+request.host+'?bod='+OpenId.secret_key
        return {'redirect': res}

    @staticmethod
    def login_required(func):
        def wrappers(*args, **kwargs):
            if not g.user:
                return abort(403)
            else:
                if not 'open_id' in g.user:
                    return abort(403)
                else:
                    if g.user.open_id != session.get('open_id'):
                        return abort(403)
                    else:
                        return func(*args, **kwargs)
        return wrappers

    @staticmethod
    def login_process(func):
        def wrap(*args, **kwargs):
            success = None
            par = parse_qs(urlparse(request.url).query)
            if 'allow' in par and par['allow'][0]:
                if 'flu' in par:
                    secret = par['flu'][0]
                    if secret == OpenId.secret_key:
                        session['open_id'] = par['open_id'][0]
                        print('success')
                        success = True
                    OpenId.secret_key = None
            res = func(*args, **kwargs)
            if request.method == 'POST' and isinstance(res, dict) and 'redirect' in res:
                return redirect(res['redirect'])
            elif success:
                return redirect(request.headers['Referer'])
            else:
                return res
        return wrap

    @staticmethod
    def after_login(func):
        def wrappers(*args, **kwargs):
            if not 'open_id' in session:
                return abort(403)
            return func(*args, **kwargs)
        return wrappers
