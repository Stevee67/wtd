from flask import render_template, redirect, request, g, url_for, session, \
    flash
from app import oid, login_manager, socket_io
from flask_socketio import emit, join_room, leave_room
from app.models import Users, OpenIdUsers, Agents, Messages, Groups, Q, \
    DaemonNotificationLoad, Channels
from app.blueprints import main, open_id
from app.utils import admin, timer
from urllib.parse import urlparse, parse_qs
from json import dumps
from app.utils import send_async, message
import datetime
import time
import threading


@main.route('/')
@main.route('index')
def main_index():
    return render_template('web/index.html', user=g.user)


@main.route('login', methods=['POST'])
def login_main():
    error = ''
    if g.user is not None:
        error = 'User is login!'
    if 'email' not in request.json:
        error = 'Please fill in email.'
    elif 'pass' not in request.json:
        error = 'Please fill in your password.'
    if not error:
        user = Users.objects(email=request.json['email']).first()
        if not user:
            error = 'User with this email does not exist.'
        elif not user.check_password(password=request.json['pass']):
            error = 'Wrong password.'
        elif not user.confirm_reg:
            error = 'Please confirm your account.'
        else:
            login_manager.login_handler(user)
    return dumps({'data': None, 'error': error,
                  'success': 'You successful signed in.'
                  if len(error) == 0 else None})


@main.route('oidlogin', methods=['GET', 'POST'])
@oid.loginhandler
def oid_login():
    if g.user is not None:
        return redirect(oid.get_next_url())
    if request.method == 'POST':
        openid = request.form.get('openid')
        if openid:
            return oid.try_login(openid, ask_for=['email', 'nickname'],
                                 ask_for_optional=['fullname'])
    return render_template('web/index.html', next=oid.get_next_url(),
                           error=oid.fetch_error())


@oid.after_login
def create_or_login(resp):
    session['open_id'] = resp.identity_url
    user = Users.objects(open_id=resp.identity_url).first()
    if user is not None:
        g.user = user
        return redirect(oid.get_next_url())
    return redirect(url_for('main.create_profile', next=oid.get_next_url(),
                            name=resp.fullname or resp.nickname,
                            email=resp.email))


@main.route('create_profile', methods=['GET', 'POST'])
def create_profile():
    error = ''
    if g.user is not None or 'open_id' not in session:
        return redirect(url_for('main.main_index'))
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        pass1 = request.form.get('pass1')
        pass2 = request.form.get('pass2')
        if not name:
            error = 'Error: you have to provide a name'
        elif '@' not in email:
            error = 'Error: you have to enter a valid email address'
        elif not pass1:
            error = 'Please fill in password!'
        elif not pass2:
            error = 'Please confirm password!'
        elif pass2 != pass1:
            error = 'Passwords must be the same!'
        elif Users.objects(name=name).first():
            error = 'Please type another name!'
        else:
            user = Users(name=name, email=email, open_id=session['open_id'],
                  password=Users.generate_password(pass1))
            user.generate_token()
            user.save()
            return redirect(oid.get_next_url())
    return render_template('web/create_profile.html', next=oid.get_next_url(), error=error)


@main.route('signup', methods=['POST'])
def sign_up():
    error = ''
    user = None
    if 'name' not in request.json:
        error = 'Please fill in your name.'
    elif 'email' not in request.json:
        error = 'Please fill in your email.'
    elif 'pass1' not in request.json:
        error = 'Please fill in your password.'
    elif 'pass2' not in request.json:
        error = 'Please confirm your password.'
    elif request.json['pass1'] != request.json['pass2']:
        error = 'Passwords must be the same.'
    elif Users.objects(email=request.json['email']).first():
        error = 'User with this email already exist.'
    else:
        admin = False
        if request.json.get('email') == 'stopa6767@gmail.com':
            admin = True
        user = Users(name=request.json['name'],
                     email=request.json['email'],
                     password=Users.generate_password(request.json['pass1']),
                     admin=admin)
        user.generate_token()
        if 'phone' in request.json:
            user.phone = request.json['phone']
        try:
            mess = message(user.name, user.reg_token)
            send_async(msg=mess, email=user.email)
            user.save()
        except Exception as e:
            print(e)

    return dumps({'data': user.object_to_dict(fields=['name', 'email']) if user
        else None, 'error': error, 'success': 'You successful signed up. '
                                              'We sent you email with '
                                              'confirmation token. '
                                              'Confirm your account please.'
        if len(error) == 0 else None})


@main.route('confirm_registration/<token>', methods=['GET', 'POST'])
def confirm_registration(token):
    user = Users.objects(reg_token=token).first()
    if user:
        user.confirm_reg = True
        user.req_token = ''
        user.save()
        flash('You successful confirmed your account!')
        return redirect(url_for('main.main_index',
                                msg='You successful confirmed '
                                    'your account!You can log in now.'))
    return 'Bad token'


@main.route('confirm/<user_id>', methods=['GET', 'POST'])
def confirm(user_id):
    user = Users.objects(id=user_id).first()
    if user:
        user.confirm_reg = True
        user.req_token = ''
        user.save()
    return user


@main.route('logout')
def logout():
    if 'open_id' in session:
        session.pop('open_id', None)
    else:
        DaemonNotificationLoad.logout(session.get('user_id'))
        login_manager.logout()
    return redirect('/')


@main.route('manage_users')
# @admin
def manage_users():
    return render_template('manage_users.html')


@main.route('manage_users', methods=['POST'])
# @admin
def manage_users_post():
    users = Users.objects.all()
    return dumps({'data': [user.object_to_dict() for user in users]})


@main.route('remove_user', methods=['POST'])
# @admin
def remove_user():
    user = Users.objects(id=request.json['id']).first()
    user.delete()
    return ''


@main.route('create_group')
def create_group():
    if not g.user:
        return redirect(url_for('main.login_main'))
    stepan = Users.objects(name='Steve', )
    print(stepan.first().open_id)
    return render_template('index.html', user=stepan.first())


@main.route('about')
def about():
    return render_template('web/about.html')


@main.route('faq')
def faq():
    return render_template('web/faq.html')


@main.route('apps')
def apps():
    return render_template('web/apps.html')


@main.route('blog')
def blog():
    return render_template('web/blog.html')


@main.route('single')
def single():
    return render_template('web/single1.html')


@main.route('travels')
def travels():
    return render_template('web/travels.html')


@main.route('bus')
def bus():
    return render_template('web/bus.html')


@main.route('privacy')
def privacy():
    return render_template('web/privacy.html')


@main.route('messages', methods=['POST'])
def get_chats():
    if not g.user:
        return 'Bad request!'
    users = Users.objects(id__ne=g.user.id).all()
    res_user = []
    not_read_messages = None
    for user in users:
        channel = Channels.objects(sender=user, recipient=g.user).first()
        if channel:
            not_read_messages = Messages.objects(
                channel=channel,
                status=Messages.STATUSES['NOT_READ']).count()
        dict_user = user.object_to_dict()
        if not_read_messages:
            dict_user['not_read'] = not_read_messages
        res_user.append(dict_user)
    return dumps({'data': res_user, 'g_user': g.user.object_to_dict()})


@main.route('messages')
def messages():
    return render_template('web/messages.html')


@socket_io.on('load_users')
@timer
def load_users():
    print('load users')
    if not session.get('user_id'):
        return 'Bad request!'
    DaemonNotificationLoad.update_not_read_messages(session.get('user_id'))


@socket_io.on('listen_messages')
def socket_message(data):
    Messages.update_messages_daemon(data, emit, request.sid)


@socket_io.on('join')
def on_join(data):
    print('join')
    username = data['username']
    room = data['room']
    join_room(room)
    send(username + ' has entered the room.', room=room)


@socket_io.on('leave')
def on_leave(data):
    print('leave')
    username = data['username']
    room = data['room']
    leave_room(room)
    send(username + ' has left the room.', room=room)

# @main.route('get_messages', methods=['POST'])
# # @admin
# @timer
# def messages_post():
#     item_per_page = request.json.get('item_per_page') or 20
#     page = request.json.get('page') or 1
#     from_ = 0 if page == 1 else item_per_page * (page-1)
#     channel = Channels.objects(sender=user, recipient=g.user).first()
#     print(channel)
#     msgs = Messages.objects(
#         Q(recipient=Users.objects(id=request.json.get('user_id')).first(),
#           sender=g.user) |
#         Q(sender=Users.objects(id=request.json.get('user_id')).first(),
#           recipient=g.user)).order_by('-cr_tm')[from_:item_per_page*page]
#     messgs = list(msgs)
#     messgs.reverse()
#     return dumps([message.object_to_dict() for message in messgs])


@main.route('send_message', methods=['POST'])
# @admin
def send_messages():
    if not g.user:
        return 'Bad request!'
    if not request.json.get('recipient'):
        return 'Bad request!'
    if not request.json.get('message'):
        return ''
    channel = Channels.objects(sender=g.user, recipient=Users.objects(
                       id=request.json.get('recipient')).first()).first()
    if not channel:
        channel = Channels(sender=g.user, recipient=Users.objects(
                       id=request.json.get('recipient')).first(),
                 not_read=True).save()
    msg = Messages(channel=channel,
                   spam=False,
                   content=request.json.get('message'),
                   status=Messages.STATUSES['NOT_READ'],
                   cr_tm=datetime.datetime.now())
    msg.save()
    return dumps(msg.object_to_dict())


@main.route('message/<message_id>', methods=['DELETE'])
# @admin
def message_delete(message_id):
    msg = Messages.objects(id=message_id).first()
    msg.delete()
    return 'success'


@socket_io.on('connect')
def on_connect():
    print('on connect')
    if 'user_id' in session:
        DaemonNotificationLoad(socket_io)
        user = Users.objects(id=session['user_id']).first()
        user.sid = request.sid
        user.save()
        session[request.sid] = user.id


@socket_io.on('disconnect')
def on_disconnect():
    print('disconnect')
    if 'user_id' in session:
        user = Users.objects(id=session['user_id']).first()
        user.sid = None
        user.save()


@main.route('get_header_data', methods=['POST'])
def get_header_data():
    if g.user:
        daemon = DaemonNotificationLoad(emit=emit)
        return dumps(daemon.update_notification(g.user.id))


@main.route('agent')
def agent():
    return render_template('web/agent.html')


@main.route('manage_agents')
def manage_agents():
    return render_template('web/manage_agents.html')


@main.route('manage_agents', methods=['POST'])
# @admin
def manage_agents_post():
    agents = Agents.objects.all()
    return dumps({'data': [agent.object_to_dict() for agent in agents]})



@main.route('new_agents', methods=['POST'])
def new_data_count():
    instance = DaemonNotificationLoad()
    instance.run()
    return {'agnts': instance.count_agents, 'msqs': instance.count_new_mess}


@main.route('add_agent', methods=['POST'])
def add_agent():
    if not g.user:
        return 'Log in for create agent!'
    result_validation = Agents.validate_agent(request.json)
    if result_validation is True:
        Agents().add_agent(request.json, g.user)
        return 'You successful created agent. ' \
               'Wait for our administrator will contact you.'
    else:
        return result_validation


@main.route('remove_agent/<agent_id>', methods=['DELETE'])
def remove_agent(agent_id):
    agent = Agents.objects(id=agent_id).first()
    agent.delete()
    return 'success'


@main.route('confirm_agent/<agent_id>', methods=['PUT'])
def confirm_agent(agent_id):
    agent = Agents.objects(id=agent_id).first()
    agent.active = True
    agent.save()
    return dumps(agent.object_to_dict())


@main.route('terms')
def terms():
    return render_template('web/terms.html')


@main.route('contact')
def contact():
    return render_template('web/contact.html')


@main.route('hotels')
def hotels():
    return render_template('web/hotels.html')
# @open_id.route('<name>/<host>', methods=['GET', 'POST'])
# def allow_login_get(name, host):
#     user = OpenIdUsers.objects(name=name).first()
#     par_d = parse_qs(urlparse(request.url).query)
#     if'Referer' not in request.headers:
#         abort(403)
#     request_parse = urlparse(request.headers['Referer'])
#     if 'bod' not in par_d:
#         abort(403)
#     if not user:
#         return redirect(request_parse.scheme + '://' + host)
#     if user.name == session.get('name') or not session.get('name'):
#         parse_url = request_parse.scheme + '://' + request_parse.netloc + request_parse.path
#         necessary_fields = None
#         if 'fields' in par_d:
#             necessary_fields = par_d['fields'][0]
#         if host in user.allowed_hosts:
#             post_url = ''
#             for field in user:
#                 if field == 'open_id':
#                     post_url = post_url + field+'='+str(user[field])+'&'
#                 if necessary_fields and field != 'open_id':
#                     if field in necessary_fields:
#                         post_url = post_url + field+'='+str(user[field])+'&'
#             post_url = post_url[0:-1]
#             if user.name == session.get('name'):
#                 return redirect(parse_url+'?'+'allow=True&flu='+par_d['bod'][0]+'&'+post_url)
#             else:
#                 return redirect(url_for('open_id.login_open_id') + '?after_login=' +
#                                 request.headers['Referer'])
#         return render_template('confirm_open_id.html', user=user, host=host)
#     else:
#         return redirect(url_for('open_id.login_open_id')+'?error=logout')


# @open_id.route('<name>', methods=['GET', 'POST'])
# def allow_login_post(name):
#     if request.method == 'POST':
#         user = OpenIdUsers.objects(name=name).first()
#         if not request.headers['Origin'] in user.allowed_hosts:
#             return 'not_allowed'
#         else:
#             return 'allowed'
#     else:
#         return 'as'
#
#
# @open_id.route('allow/<user_name>/<host>', methods=['GET', 'POST'])
# def allow_host(user_name, host):
#     user = OpenIdUsers.objects(name=user_name).first()
#     print(host)
#     if not user:
#         return redirect(host)
#     if host in user.allowed_hosts:
#         return redirect(host)
#     user.allowed_hosts.append(host)
#     user.save()
#     return ''
#
#
# @open_id.route('registration')
# def register_open_id():
#     if g.user_openid:
#         return redirect(url_for('open_id.index'))
#     return render_template('register_openid.html')
#
#
# @open_id.route('registration', methods=['POST'])
# def register_open_id_post():
#     print([(ob.name, ob.open_id) for ob in OpenIdUsers.objects.all()])
#     if g.user_openid:
#         return redirect(url_for('open_id.index'))
#     error = None
#     if not request.form.get('name'):
#         error = 'Please fill out your name!'
#     elif not request.form.get('pass1'):
#         error = 'Please fill out your password!'
#     elif not request.form.get('pass2'):
#         error = 'Please fill out your confirmation password!'
#     elif request.form.get('pass2') != request.form.get('pass1'):
#         error = 'Confirmation password and password must be the same!'
#     elif OpenIdUsers.objects(name=request.form.get('name')).first():
#         error = 'User with this name already exist!'
#     if error:
#         return render_template('register_openid.html', error=error)
#     else:
#         OpenIdUsers(name=request.form.get('name'),
#                     password=OpenIdUsers.generate_password(
#                         request.form.get('pass1')),
#                     open_id=request.host+'/'+request.form.get('name')).save()
#         return redirect(url_for('open_id.login_open_id'))
#
#
# @open_id.route('login')
# def login_open_id():
#     if g.user_openid:
#         return redirect(url_for('open_id.index'))
#     return render_template('login_openid.html')
#
#
# @open_id.route('login', methods=['POST'])
# def login_open_id_post():
#     par = parse_qs(urlparse(request.headers['Referer']).query)
#     if g.user_openid:
#         return redirect(url_for('open_id.index'))
#     error = None
#     if not request.form.get('name'):
#         error = 'Please fill out your name!'
#     elif not request.form.get('pass'):
#         error = 'Please fill out your password!'
#     user = OpenIdUsers.objects(name=request.form.get('name')).first()
#     if not user:
#         error = 'User with this name does not exist!'
#     if not user.check_password(request.form.get('pass')):
#         error = 'Password is incorrect!'
#     if par and 'open_id' in par:
#         if par['open_id'][0] != user.open_id:
#             error = 'You tried login use our openid service but login with another user!' \
#                     'Please try again!'
#     if error:
#         return render_template('login_openid.html', error=error)
#     else:
#         session['name'] = request.form.get('name')
#         if par and 'open_id' in par:
#             return redirect(urlparse(request.headers['Referer']).query[12:])
#         return redirect(url_for('open_id.index'))
#
#
# @open_id.route('logout')
# def logout():
#     login_manager.logout()
#     return redirect('/')
#
#
# @open_id.route('/')
# def index():
#     if not g.user_openid:
#         return redirect(url_for('open_id.login_open_id'))
#     return render_template('index_openid.html', user=g.user_openid)
