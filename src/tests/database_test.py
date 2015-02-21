from src.db.database import Database

__author__ = 'jslvtr'

import unittest


class DatabaseTest(unittest.TestCase):

    def setUp(self):
        self.database = Database('mongodb://admin:admin@ds063879.mongolab.com:63879/heroku_app34205970')

    def test_insert_and_find(self):
        collection = self.database.db['test']
        collection.insert({'name': 'Jose'})
        self.assertTrue(collection.find({'name': 'Jose'})[0], {'name': 'Jose'})

    def test_find_one(self):
        collection = self.database.db['test']
        collection.insert({'name': 'Jose'})
        self.assertTrue(collection.find_one({'name': 'Jose'}), {'name': 'Jose'})

    def test_delete(self):
        collection = self.database.db['test']
        collection.remove({'name': 'Jose'})
        self.assertIsNone(collection.find_one({'name': 'Jose'}))


if __name__ == '__main__':
    unittest.main()
