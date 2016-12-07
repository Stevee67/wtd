from flask import abort, g, request
from functools import wraps
from config import Config
import smtplib
import threading
import time


def admin(func):
    @wraps(func)
    def wrappers(*args, **kwargs):
        if g.user:
            if g.user.admin is not True:
                abort(403)
            else:
                return func(*args, **kwargs)
        else:
            abort(403)
    return wrappers


def send_message(message, email, password=Config.MAIL_PASS):
    from_addr = Config.SENDER_ADDRESS
    toaddrs = email
    message = 'Subject: confirm registration\n\n' + message
    username = Config.SENDER_ADDRESS
    server = smtplib.SMTP(Config.MAIL_SERVER+':'+Config.MAIL_PORT)
    server.starttls()
    server.login(username, password)
    server.sendmail(from_addr, toaddrs, message)
    server.quit()


def message(name, token):
    link = 'http://{0}/confirm_registration/{1}'.format(request.host, token)
    return """Hi {0} \n
    Thanks for getting started with Whattodo! We need a little more
    information \n
    to complete your registration, including confirmation of your email
    address. \n
    Click below to confirm your email address: {1}. \n
    If you have problems, please paste the above URL
    into your web browser.'""".format(name, link)


def send_async(msg, email=Config.SENDER_ADDRESS):
    sender = threading.Thread(target=send_message,
                              args=(msg, email))
    sender.start()


def timer(func):
    @wraps(func)
    def wrappers(*args, **kwargs):
        start = time.clock()
        result = func(*args, **kwargs)
        end = time.clock()
        print(end-start)
        return result

    return wrappers
