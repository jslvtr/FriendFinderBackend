from flask import Flask, request, abort, g
from src.db.models import Beacon, User
from src.db.database import Database
import datetime

app = Flask(__name__,)


def log(to_write):
    print("{} {}".format(datetime.datetime.now().strftime("%b %d %H:%M:%S"),
                         to_write))


@app.before_request
def init_db():
    g.database = Database('mongodb://admin:admin@ds063879.mongolab.com:63879/heroku_app34205970')


@app.route('/')
def hello():
    return 'hello'


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


@app.route('/beacons/add', methods=['POST'])
def add_beacon():
    beacon_id = request.json.get('id')
    room_id = request.json.get('room_id')
    name = request.json.get('name')
    location = request.json.get('location')

    if not(beacon_id and room_id and name and location):
        abort(400)

    return Beacon.create()


if __name__ == '__main__':
    app.run()