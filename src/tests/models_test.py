from flask import g
from src.db.database import Database

__author__ = 'jslvtr'

import unittest
from src.db.models import email_is_valid, Provider, User
from src.app.FriendFinderBackend import app, init_db

class ModelsTest(unittest.TestCase):

    def setUp(self):
        self.stuart_twitter_access_token = "GTvMXibcnUYoMDnD2MTaRD5xp"
        self.stuart_twitter_access_secret = "16DaykgV8kMWGr5WOBhUd0u1l4cpVvfP7ttnY9Qu2XC4trFZkJ"
        self.app_context = app.app_context()
        with self.app_context:
            g.database = Database('mongodb://admin:admin@ds063879.mongolab.com:63879/heroku_app34205970')

    def tearDown(self):
        with self.app_context:
            g.database = None

    def test_email_is_valid(self):
        self.assertTrue(email_is_valid('jslvtr@gmail.com'))

    def test_beacon_add(self):
        self.assertTrue(True)

    def test_create_provider(self):
        twitter_dict = Provider.create("Twitter",
                                       self.stuart_twitter_access_token,
                                       self.stuart_twitter_access_secret).to_dict()

        self.assertEqual(twitter_dict['name'], "Twitter")
        self.assertEqual(twitter_dict['access_token'], self.stuart_twitter_access_token)

    def test_create_user(self):
        user_dict = self._sample_user().to_dict()

        self.assertEqual(user_dict['username'], "jslvtr")
        self.assertEqual(user_dict['id'], "15685156")
        self.assertEqual(user_dict['providers'][0].to_dict(),
                         Provider.create("Twitter", self.stuart_twitter_access_token,
                                         self.stuart_twitter_access_secret).to_dict())

    def test_save_user(self):
        user = self._sample_user()
        with self.app_context:
            user.save()
            User.remove(user.id)

    def test_find_twitter_user(self):
        user = self._sample_user()
        with self.app_context:
            user.save()
            self.assertEqual(User.get_by_provider("Twitter", self.stuart_twitter_access_token).id,
                             self._sample_user().id)
            self.assertEqual(User.get_by_provider("Twitter", self.stuart_twitter_access_token).username,
                             self._sample_user().username)
            self.assertEqual(User.get_by_provider("Twitter", self.stuart_twitter_access_token).email,
                             self._sample_user().email)
            self.assertEqual(User.get_by_provider("Twitter", self.stuart_twitter_access_token).providers,
                             self._sample_user().providers)
            User.remove(user.id)

    def _sample_user(self):
        user = User.create(username="jslvtr",
                           user_id="15685156",
                           provider_name="Twitter",
                           access_token=self.stuart_twitter_access_token,
                           access_secret=self.stuart_twitter_access_secret)
        return user

if __name__ == '__main__':
    unittest.main()
