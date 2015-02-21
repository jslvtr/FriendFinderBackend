__author__ = 'jslvtr'

import pymongo
import pymongo.errors


class Database(object):
    def __init__(self, uri):
        client = pymongo.MongoClient(uri)
        self.db = client.get_default_database()
        self.collection = None

    def insert(self, data):
        if self.collection is not None:
            self.collection.insert(data)
        else:
            raise pymongo.errors.InvalidOperation

    def remove(self, data):
        if self.collection is not None:
            self.collection.remove(data)
        else:
            raise pymongo.errors.InvalidOperation

    def update(self, query, data):
        if self.collection is not None:
            self.collection.update(query, data)
        else:
            raise pymongo.errors.InvalidOperation

    def find(self, query=None):
        if self.collection is not None:
            if query is None:
                return self.collection.find()
            else:
                return self.collection.find(query)
        else:
            raise pymongo.errors.InvalidOperation

    def find_one(self, query):
        if self.collection is not None:
            return self.collection.find_one(query)
        else:
            raise pymongo.errors.InvalidOperation

    def close(self):
        self.db.close()
