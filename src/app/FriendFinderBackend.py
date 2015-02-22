from flask import Flask, request, abort, g
from src.db.models import Group, User
from src.db.database import Database
import datetime

app = Flask(__name__,)


def log(to_write):
    print("{} {}".format(datetime.datetime.now().strftime("%b %d %H:%M:%S"),
                         to_write))


@app.before_request
def init_db():
    g.database = Database('mongodb://admin:admin@ds063879.mongolab.com:63879/heroku_app34205970')


@app.route('/login/twitter', methods=['POST'])
def login_twitter():

    log("Logging in with Twitter.")

    username = request.json.get('username')
    user_id = request.json.get('user_id')
    provider_name = request.json.get('provider_name')
    access_token = request.json.get('access_token')
    access_secret = request.json.get('access_secret')

    log("Twitter username: {}\nID: {}.".format(username,
                                               user_id))

    user = User.create(username, provider_name, access_token, access_secret, user_id=user_id)
    log("Created Twitter user.")
    user.save()
    log("Saved Twitter user to database.")


@app.route('/login/facebook', methods=['POST'])
def login_facebook():
    email = request.json.get('email')
    username = request.json.get('name')
    provider_name = request.json.get('provider_name')
    access_token = request.json.get('access_token')
    access_secret = request.json.get('access_secret')

    user = User.create(username, provider_name, access_token, access_secret, email=email)
    user.save()


@app.route('/user/location', methods=['POST'])
def update_user_location():
    lat = request.json.get('lat')
    lon = request.json.get('lon')
    user_id = request.json.get('id')

    User.update(user_id, lat, lon)


# @app.route('/group/<group_id>/locations')
# def get_friend_locations(group_id):
#     group = Group.get_by_id(group_id)
#
#     ret = []
#
#     for friend_id in group.users:
#         ret.extend([User.get_by_id(friend_id).location])
#
#     return ret


@app.route('/group/<group_id>/add')
def add_member_to_group(group_id):

    user_id = request.json.get('user_id')

    group = Group.get_by_id(group_id)
    Group.add_member(group.id, user_id)


if __name__ == '__main__':
    app.run()