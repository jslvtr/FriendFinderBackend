import random
import re
import uuid

from hashlib import sha1
from bson.son import SON
from datetime import datetime

from flask import g
from werkzeug.security import generate_password_hash, check_password_hash
from bson.binary import Binary

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def email_is_valid(email):
    address = re.compile('^[\w\d.+-]+@([\w\d.]+\.)+[\w]+$')
    return True if address.match(email) else False


class ModelBase(object):
    collection = None

    @staticmethod
    def generate_id():
        return uuid.uuid4().hex

    @classmethod
    def db(cls):
        g.database.collection = g.database.db[cls.collection]
        return g.database

    @classmethod
    def get_by_id(cls, model_id):
        query = {'id': model_id}
        data = cls.db().find_one(query)

        return cls(data) if data else None

    @classmethod
    def get_all(cls, query=None):
        if query is None:
            documents = cls.db().find()
        else:
            documents = cls.db().find(query)

        return [cls(document) for document in documents]


class Field(object):
    def __init__(self, key, default=None, visible=True):
        self.key = key
        self.default = default
        self.visible = visible


class FieldManagerMixin(object):
    fields = []

    def __init__(self, data=None):
        self._data = SON()

        if data is not None:
            for field in self.fields:
                key = field.key
                self._data[key] = data.get(key, field.default)

    def __getattr__(self, name):
        if name in self._data:
            return self._data[name]
        else:
            raise AttributeError

    def __setattr__(self, name, value):
        if name != '_data' and name in self._data:
            self._data[name] = value
        else:
            object.__setattr__(self, name, value)

    def to_dict(self):
        data = SON()

        for field in self.fields:
            if field.visible:
                key = field.key
                data[key] = self._data[key]

        return data


class Room(FieldManagerMixin):
    collection = 'rooms'
    fields = [
        Field('id'),
        Field('size', default={'width': 0, 'height': 0, 'floors': 0}),
        Field('image')
    ]

    @classmethod
    def from_dict(cls, dictionary):
        data = {
            'id': dictionary['id'],
            'size': dictionary['size'],
            'image': Binary(dictionary['image'])
        }

        return cls(data)


class Group(ModelBase, FieldManagerMixin):

    class CalledEmptyUpdate(Exception):
        pass

    collection = 'groups'

    fields = [
        Field('id'),
        Field('users', default=[]),
        Field('name')
    ]

    @classmethod
    def from_dict(cls, dictionary):
        data = {
            'id': dictionary['id'],
            'users': dictionary['users'],
            'name': dictionary['name']
        }

        return cls(data)

    @classmethod
    def create(cls, group_id, name, creator):
        data = {'id': group_id,
                'name': name,
                'users': [creator]}

        return cls(data)

    @classmethod
    def get_by_id(cls, model_id):
        query = {'id': model_id}
        data = cls.db().find_one(query)

        return cls(data) if data else None

    @classmethod
    def get_by_user_id(cls, user_id):
        query = {'users': {'$in': user_id}}
        data = cls.db().find_one(query)

        return cls(data) if data else None

    @classmethod
    def remove(cls, group_id):
        query = {'id': group_id}

        cls.db().remove(query)

    def save(self):
        data = SON()
        data.update(self._data)
        self.db().insert(data)

    @classmethod
    def add_member(cls, group_id, new_user_id):
        if group_id is None or new_user_id is None:
            raise cls.CalledEmptyUpdate
        cls.db().update({'id': group_id}, {'$addToSet': {'users': new_user_id}})

    @classmethod
    def remove_member(cls, group_id, user_id):
        if group_id is None or user_id is None:
            raise cls.CalledEmptyUpdate
        cls.db().update({'id': group_id}, {'$pull': {'users': user_id}})


class Provider(ModelBase, FieldManagerMixin):

    fields = [
        Field('name'),
        Field('access_token'),
        Field('access_secret')
    ]

    @classmethod
    def create(cls, name, access_token, access_secret):
        data = {'name': name,
                'access_token': access_token,
                'access_secret': access_secret
        }

        return cls(data)


class User(ModelBase, FieldManagerMixin):

    class EmailAlreadyInUse(Exception):
        pass

    class IncorrectEmailOrPassword(Exception):
        pass

    class CalledEmptyUpdate(Exception):
        pass

    class EmptyEventAdded(Exception):
        pass

    class UserNotExists(Exception):
        pass

    collection = 'users'

    fields = [
        Field('id'),
        Field('username'),
        Field('name'),
        Field('email'),
        Field('password', visible=False),
        Field('providers', default=[]),
        Field('access_token'),
        Field('last_request'),
        Field('location', default=[]),
        Field('joined_date')
    ]

    @staticmethod
    def generate_access_token():
        random_bytes = [chr(random.randrange(256)) for i in range(16)]
        random_bytes = "".join(random_bytes)
        return sha1(random_bytes).hexdigest()

    @classmethod
    def get_by_id(cls, model_id):
        query = {'id': model_id}
        data = cls.db().find_one(query)

        return cls(data) if data else None

    @classmethod
    def get_by_email(cls, model_email):
        query = {'email': model_email}
        data = cls.db().find_one(query)

        return cls(data) if data else None

    @classmethod
    def get_by_access_token(cls, model_access_token):
        query = {'access_token': model_access_token}
        data = cls.db().find_one(query)

        return cls(data) if data else None

    @classmethod
    def create(cls, email, password):
        data = {'id': cls.generate_id(),
                'access_token': cls.generate_access_token(),
                'joined_date': datetime.utcnow(),
                'email': email,
                'password': generate_password_hash(password)}

        return cls(data)

    @classmethod
    def get_by_provider(cls, provider, access_token):
        query = {'providers.name': provider,
                 'providers.access_token': access_token}
        data = cls.db().find_one(query)

        return cls(data) if data else None

    @classmethod
    def register(cls, email, password):
        # Check if user exists
        if cls.get_by_email(email) is None:
            return cls.create(email, password)

        raise cls.EmailAlreadyInUse

    @classmethod
    def login(cls, email, password):
        user_data = cls.db().find_one({'email': email})

        if user_data is not None and len(user_data) > 0:
            is_valid = (
                user_data and
                user_data['password'] and
                check_password_hash(user_data['password'], password)
            )

            if not is_valid:
                raise cls.IncorrectEmailOrPassword

            return cls(user_data)
        raise cls.UserNotExists

    @classmethod
    def update_location(cls, user_id, lat, lon):
        if lat is None or lon is None:
            raise cls.CalledEmptyUpdate
        cls.db().update({'id': user_id}, {'$set': {'location': [lat, lon]}})

    def save(self):
        data = SON()
        data.update(self._data)
        self.db().insert(data)

    @classmethod
    def remove(cls, user_id):
        query = {'id': user_id}

        cls.db().remove(query)

class Invite(ModelBase, FieldManagerMixin):
    collection = 'invites'
    fields = [
        Field('email'),
        Field('inviter_id'),
        Field('token'),
        Field('created_date'),
        Field('pending')
    ]

    @staticmethod
    def generate_access_token():
        random_bytes = [chr(random.randrange(256)) for i in range(16)]
        random_bytes = "".join(random_bytes)
        return sha1(random_bytes).hexdigest()

    @classmethod
    def create(cls, email, inviter_id):
        data = {'email': email,
                'inviter_id': inviter_id,
                'token': cls.generate_access_token(),
                'created_date': datetime.utcnow(),
                'pending': True
        }

        return cls(data)

    @classmethod
    def activate(cls, token, password):
        invite = cls.get_by_token(token)
        email = invite.email
        user = User.register(email, password)
        user.save()
        Group.add_member(invite.inviter_id, user.id)

        Invite.mark_complete(email)

    def save(self):
        data = SON()
        data.update(self._data)
        self.db().insert(data)

    @classmethod
    def get_by_email(cls, model_email):
        query = {'email': model_email}
        data = cls.db().find_one(query)

        return cls(data) if data else None

    @classmethod
    def get_by_token(cls, model_token):
        query = {'token': model_token}
        data = cls.db().find_one(query)

        return cls(data) if data else None

    @classmethod
    def mark_complete(cls, model_email):
        if model_email is not None:
            cls.db().update({'email': model_email}, {'$set': {'pending': False}})

    def send(self):
        smtp_user = "friendfinderbeacons@gmail.com"
        smtp_password = "stackshack"
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        receiver = self.email

        msg = MIMEMultipart('alternative')

        msg['From'] = smtp_user
        msg['To'] = self.email
        msg['Subject'] = "You've been invited to FriendFinder!"

        message = "Please register your account <a href=\"http://friend-finder-beacons.herokuapp.com/confirm/" + self.token + "\">here</a>.<br/>"
        message += "If you can't see this link please go to {}".format("http://friend-finder-beacons.herokuapp.com/confirm/" + self.token)

        try:
            # Create SMTP object
            smtpObj = smtplib.SMTP(smtp_server, smtp_port)

            # Send EHLO or HELO greeting so server recognizes us
            smtpObj.ehlo()
            smtpObj.starttls()
            smtpObj.ehlo()
            smtpObj.login(smtp_user, smtp_password)

            msg.attach(MIMEText(message, 'html'))

            # Log-in to the server with the config sender/password
            # smtpObj.login(sender, smtp_password)

            # Send e-mail to receivers.
            smtpObj.sendmail(smtp_user, receiver, msg.as_string())

            smtpObj.quit()
            print "Successfully sent email"
        except smtplib.SMTPException:
            print "Error: unable to send email"