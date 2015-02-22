from flask import g
from src.db.database import Database
from werkzeug.security import check_password_hash

__author__ = 'jslvtr'

import unittest
from src.db.models import email_is_valid, Provider, User, Group
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
        user = self._sample_user()

        self.assertEqual(user.email, "jslvtr@gmail.com")
        self.assertTrue(check_password_hash(user.password, "jose"))

    def test_register_user(self):
        with self.app_context:
            user = User.register(email="paco@paco.com",
                                 password="paco")

            user.save()

            user_test = User.get_by_id(user.id)
            self.assertIsNotNone(user_test.access_token)
            self.assertEqual(user.email, "paco@paco.com")
            self.assertTrue(check_password_hash(user.password, "paco"))

            User.remove(user.id)

    def test_save_user(self):
        user = self._sample_user()
        with self.app_context:
            user.save()
            User.remove(user.id)

    def test_update_user_location(self):
        user = self._sample_user()

        with self.app_context:
            user.save()

            User.update_location(user.id, 57.062, 13.673)

            user_test = User.get_by_id(user.id)
            self.assertEqual(user_test.location[0], 57.062)
            self.assertEqual(user_test.location[1], 13.673)
            User.remove(user.id)

    def test_get_groups_of_user(self):
        pass

    # def test_find_twitter_user(self):
    #     user = self._sample_user()
    #     with self.app_context:
    #         user.save()
    #         self.assertEqual(User.get_by_provider("Twitter", self.stuart_twitter_access_token).id,
    #                          self._sample_user().id)
    #         self.assertEqual(User.get_by_provider("Twitter", self.stuart_twitter_access_token).username,
    #                          self._sample_user().username)
    #         self.assertEqual(User.get_by_provider("Twitter", self.stuart_twitter_access_token).email,
    #                          self._sample_user().email)
    #         self.assertEqual(User.get_by_provider("Twitter", self.stuart_twitter_access_token).providers,
    #                          self._sample_user().providers)
    #         User.remove(user.id)

    def _sample_user(self):
        user = User.create(email="jslvtr@gmail.com",
                           password="jose")
        return user

    def _sample_group(self, creator):
        group = Group.create(group_id="1234",
                             creator=creator.id,
                             name="Test group")
        return group

    def test_create_group(self):
        group_dict = self._sample_group(self._sample_user()).to_dict()

        self.assertEqual(group_dict['id'], "1234")
        self.assertEqual(group_dict['name'], "Test group")

    def test_add_member_to_group(self):
        user = self._sample_user()
        group = self._sample_group(user)

        with self.app_context:
            Group.remove(group.id)
            User.remove(user.id)

            user.save()
            group.save()

            Group.add_member(group.id, "1234")

            group_test = Group.get_by_id(group.id)

            Group.remove(group.id)
            User.remove(user.id)

            self.assertTrue("1234" in group_test.users)

    def test_get_group_members(self):
        user = self._sample_user()
        group = self._sample_group(user)

        with self.app_context:

            Group.remove(group.id)
            User.remove(user.id)

            user.save()
            group.save()

            ret = []

            for friend_id in group.users:
                friend = User.get_by_id(friend_id)
                ret.extend([{'friend_id': friend_id,
                             'name': friend.email,
                             'location': friend.location}])

            self.assertGreater(len(ret), 0)

            Group.remove(group.id)
            User.remove(user.id)


if __name__ == '__main__':
    unittest.main()
