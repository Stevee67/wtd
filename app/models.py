from werkzeug.security import generate_password_hash, check_password_hash
from mongoengine import StringField, ListField, BooleanField, ReferenceField, \
    DateTimeField, Q, IntField
from flask_mongoengine import Document
import datetime
from config import Config
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import time


class Base:

    children = ()

    def __new__(cls, *args, **kwargs):
        cls = super(Base, cls).__new__(
            cls, *args)
        if not cls.__class__ in Base.children:
            Base.children += (cls.__class__, )
        return cls


    @staticmethod
    def immut_to_dict(imut):
        ret_dict = {}
        iters = dict(imut)
        for k in iters:
            ret_dict[k] = iters[k][0]
        return ret_dict

    def object_to_dict(self, fields=None):
        ret_dict = {}
        for attr in self._db_field_map.keys():
            value = self.__getattribute__(attr)
            if isinstance(value, datetime.datetime):
                value = str(value)
            if attr == 'id':
                ret_dict['id'] = str(value)
            else:
                if attr != 'password':
                    if fields:
                        if attr in fields:
                            ret_dict[attr] = value
                    else:
                        if isinstance(value, Base.children):
                            ret_dict[attr] = Base.object_to_dict(value, fields)
                        else:
                            ret_dict[attr] = value
        return ret_dict


class Users(Document, Base):

    country = StringField(max_length=200)
    password = StringField(max_length=128)
    group = StringField(max_length=200)
    name = StringField(max_length=200)
    open_id = StringField(max_length=200)
    admin = BooleanField(default=False)
    banned = BooleanField(default=False)
    email = StringField(max_length=200, unique=True)
    phone = StringField(max_length=200)
    confirm_reg = BooleanField(default=False)
    reg_token = StringField(max_length=500)
    reset_token = StringField(max_length=500)
    cr_tm = DateTimeField(default=datetime.datetime.now())
    md_tm = DateTimeField(default=datetime.datetime.now())
    sid = StringField(max_length=200)

    @staticmethod
    def generate_password(password):
        return generate_password_hash(password, method='pbkdf2:sha256',
                                      salt_length=32)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def generate_token(self, expiration=100):
        s = Serializer(Config.SECRET_KEY, expiration)
        self.reg_token = s.dumps({'user': str(self.email)}).decode('utf-8')

    def verify_token(self, token):
        return self.reg_token == token

    def get_id(self):
        return str(self.id)


class Agents(Document, Base):

    name = StringField(max_length=200, required=True, unique=True)
    country = StringField(max_length=200, required=True)
    state = StringField(max_length=200)
    city = StringField(max_length=200, required=True)
    organization = StringField(max_length=200, required=True)
    email = StringField(max_length=200, required=True)
    user = ReferenceField(Users, required=True)
    phone = StringField(max_length=200, required=True)
    banned = BooleanField(default=False)
    active = BooleanField(default=False)
    message = StringField(required=True)
    cr_tm = DateTimeField(default=datetime.datetime.now())
    md_tm = DateTimeField(default=datetime.datetime.now())

    ORDERED_FIELDS = ['name', 'email', 'organization', 'country', 'city',
                      'phone', 'message']
    ORDERED_FIELD_ERROR = {
        'name': 'Please fill in name of agent.',
        'email': 'Please fill in email of your organization.',
        'organization': 'Please fill in your organization.',
        'country': 'Please fill in country.',
        'city': 'Please fill in city.',
        'phone': 'Please fill in phone of your organization.',
        'message': 'Please fill in message. We want some information from you.'}

    @staticmethod
    def validate_agent(request):
        if not request:
            return 'Fill in form.'
        for required in Agents.ORDERED_FIELDS:
            if not request.get(required):
                return Agents.ORDERED_FIELD_ERROR[required]
        else:
            return True

    def add_agent(self, request, user):
        for key, value in request.items():
            self.__setattr__(key, value)
        self.user = user
        try:
            self.save()
        except Exception as e:
            print(e)
        return self


class Channels(Document, Base):

    sender = ReferenceField(Users)
    recipient = ReferenceField(Users)
    not_read = IntField()

    def create_chanel(self, users_id):
        self.users = [id for id in users_id]
        print(self.users)


class Groups(Document, Base):

    users = ListField(ReferenceField(Users))
    title = StringField(max_length=500, unique=True, required=True)
    owner = StringField(max_length=200, required=True)

    def create_group(self, users_id, owner, title):
        self.users = [id for id in users_id]
        print(self.users)


class Messages(Document, Base):

    content = StringField(required=True)
    status = StringField(max_length=50, required=True)
    spam = BooleanField(default=False)
    cr_tm = DateTimeField(default=datetime.datetime.now())
    channel = ReferenceField(Channels)
    group = ReferenceField(Groups)
    STATUSES = {'NOT_READ': 'NOT_READ', 'READ': 'READ'}

    def send_message(self, content, user):
        pass


class OpenIdUsers(Document):

    name = StringField(max_length=200, unique=True)
    password = StringField(max_length=128)
    open_id = StringField(max_length=200, unique=True)
    email = StringField(max_length=200)
    sender = StringField(max_length=200)
    banned = BooleanField(default=False)
    allowed_hosts = ListField(StringField(max_length=300, unique=True))

    @staticmethod
    def generate_password(password):
        return generate_password_hash(password,
                                      method='pbkdf2:sha256',
                                      salt_length=32)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    @staticmethod
    def if_correct_dict_hosts(dict):
        pass


class DaemonNotificationLoad:
    socket_io = None
    socket_on_close = ''

    _users = set()

    def __init__(self, socket_io):
        DaemonNotificationLoad.socket_io = socket_io

    @staticmethod
    def update_notification(uid, sid):
        new_m = None
        new_a = None
        user = Users.objects(id=uid).first()
        if user:
            if user.get_id() not in DaemonNotificationLoad._users:
                DaemonNotificationLoad._users.add(user.get_id())
            while True:
                if user.get_id() not in DaemonNotificationLoad._users:
                    break
                count_agents = 0
                count_new_mess = Messages.objects(recipient=user,
                                                       status=Messages.STATUSES[
                                                           'NOT_READ']).count()
                if user.admin:
                    count_agents = Agents.objects(active=False).count()
                if new_m is None or new_m != count_new_mess or new_a is None or new_a != count_agents:
                    new_m = count_new_mess
                    new_a = count_agents
                    DaemonNotificationLoad.socket_io.emit(
                        'update_load', {'nmsgs': count_new_mess,
                                        'nagnts': count_agents},
                                        room=sid)
                time.sleep(2)

    @staticmethod
    def logout(uid):
        sids = list(DaemonNotificationLoad._users)
        if sids:
            print(sids)
            index = sids.index(uid)
            if index != -1:
                DaemonNotificationLoad._users.remove(uid)

    @staticmethod
    def update_not_read_messages(current_user_id):
        users = Users.objects(id__ne=current_user_id).all()
        g_user = Users.objects(id=current_user_id).first()
        res_user = []
        for user in users:
            not_read_messages = Messages.objects(
                channel = '',
                status=Messages.STATUSES['NOT_READ']).count()
            dict_user = user.object_to_dict()
            dict_user['not_read'] = not_read_messages
            res_user.append(dict_user)
        new_m = None
        new_a = None
        while True:
            count_agents = 0
            user = Users.objects(id=uid).first()
            if user:
                count_new_mess = Messages.objects(recipient=user,
                                                  status=Messages.STATUSES[
                                                      'NOT_READ']).count()
                if user.admin:
                    count_agents = Agents.objects(active=False).count()
                if new_m is None or new_m != count_new_mess or new_a is None or new_a != count_agents:
                    new_m = count_new_mess
                    new_a = count_agents
                    DaemonNotificationLoad.socket_io.emit(
                        'update_load', {'nmsgs': count_new_mess,
                                        'nagnts': count_agents},
                        room=sid)
                time.sleep(2)

