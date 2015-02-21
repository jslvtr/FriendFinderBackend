import random
import re
import uuid

from hashlib import sha1
from bson.son import SON
from datetime import datetime

from flask import g
from werkzeug.security import generate_password_hash, check_password_hash
from bson.binary import Binary


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


class Beacon(FieldManagerMixin):

    collection = 'beacons'

    fields = [
        Field('id'),
        Field('room_id'),
        Field('name'),
        Field('location', default={'x': 0, 'y': 0, 'z': 0})
    ]

    @classmethod
    def from_dict(cls, dictionary):
        data = {
            'id': dictionary['id'],
            'room_id': dictionary['room_id'],
            'name': dictionary['name'],
            'location': dictionary['location']
        }

        return cls(data)


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
        Field('providers', default=[]),
        Field('access_token'),
        Field('last_request'),
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

        print("{}".format(query))
        return cls(data) if data else None

    @classmethod
    def get_by_access_token(cls, model_access_token):
        query = {'access_token': model_access_token}
        data = cls.db().find_one(query)

        return cls(data) if data else None

    @classmethod
    def create(cls, username, user_id, provider_name, access_token, access_secret):
        data = {'id': user_id,
                'providers': [Provider.create(provider_name, access_token, access_secret).to_dict()],
                'access_token': cls.generate_access_token(),
                'joined_date': datetime.utcnow(),
                'username': username}

        return cls(data)

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
    def update(cls, email, extra_data):
        if extra_data is None:
            raise cls.CalledEmptyUpdate
        cls.db().update({'email': email}, {'$set': extra_data})

    def save(self):
        data = SON()
        data.update(self._data)
        self.db().insert(data)