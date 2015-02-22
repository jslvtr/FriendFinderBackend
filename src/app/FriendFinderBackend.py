from functools import wraps
from flask import Flask, request, abort, g, jsonify
from src.db.models import Group, User, email_is_valid
from src.db.database import Database
from flask.ext.cors import CORS, cross_origin
import datetime

app = Flask(__name__,)
cors = CORS(app)
app.config['CORS_HEADERS'] = ['Content-Type', 'Authorization', 'Accept']


def log(to_write):
    print("{} {}".format(datetime.datetime.now().strftime("%b %d %H:%M:%S"),
                         to_write))


@app.before_request
def init_db():
    g.database = Database('mongodb://admin:admin@ds063879.mongolab.com:63879/heroku_app34205970')


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        authorization = request.headers.get('Authorization')

        if not check_authorization(authorization):
            abort(403)

        return f(*args, **kwargs)

    return decorated

# @app.route('/login/twitter', methods=['POST'])
# def login_twitter():
#
#     log("Logging in with Twitter.")
#
#     username = request.json.get('username')
#     user_id = request.json.get('user_id')
#     provider_name = request.json.get('provider_name')
#     access_token = request.json.get('access_token')
#     access_secret = request.json.get('access_secret')
#
#     log("Twitter username: {}\nID: {}.".format(username,
#                                                user_id))
#
#     user = User.create(email, password)
#     log("Created Twitter user.")
#     user.save()
#     log("Saved Twitter user to database.")


def check_authorization(authorization):
    if authorization is not None:
        try:
            ffinder, access_key = authorization.split(' ')
        except ValueError:
            return False

        if ffinder != 'FFINDER':
            return False

        try:
            g.user = User.get_by_access_key(access_key)
        except User.DoesNotExist:
            return False

        return True


def create_response_data(data, status_code):
    return {
        'data': data,
        'status_code': status_code
    }


def create_response_error(error_name, error_message, status_code):
    return {
        'error': {
            'name': error_name,
            'message': error_message
        },
        'status_code': status_code
    }

@app.route('/users/register', methods=['POST'])
@cross_origin(headers=['Content-Type', 'Authorization', 'Accept'])
def register_user():
    email = request.json.get('email')
    password = request.json.get('password')

    if not email_is_valid(email):
        response_data = create_response_error(
            'InvalidEmail',
            'This email is invalid',
            409
        )

        return jsonify(response_data)

    if not password:
        response_data = create_response_error(
            'InvalidPassword',
            'This password is invalid',
            409
        )

        return jsonify(response_data)

    try:
        user = User.register(email, password)
    except User.EmailAlreadyInUse:
        response_data = create_response_error(
            'UsedEmail',
            'This email is already in use',
            409
        )
        return jsonify(response_data)

    user.save()

    # Create a Friends default group for the user
    # This group has the same id as the user id
    friends_group = Group.create(group_id=user.id,
                                 name="Friends",
                                 creator=user.id)

    friends_group.save()

    response_data = create_response_data(
        user.to_dict(),
        200
    )
    return jsonify(response_data), response_data['status_code']

@app.route('/users/login', methods=['POST'])
@cross_origin(headers=['Content-Type', 'Authorization', 'Accept'])
def login_user():
    email = request.json.get('email')
    password = request.json.get('password')

    if not (email or password):
        response_data = create_response_error(
            'EmptyEmailOrPassword',
            'The email or password is empty',
            409
        )
        return jsonify(response_data)

    try:
        user = User.login(email, password)
    except User.IncorrectEmailOrPassword:
        response_data = create_response_error(
            'IncorrectEmailOrPassword',
            'The email or password is incorrect',
            409
        )
        return jsonify(response_data)

    except User.UserNotExists:
        response_data = create_response_error(
            'UserNotExists',
            'The user was not found in the database!',
            409
        )
        return jsonify(response_data)

    response_data = create_response_data(
        user.to_dict(),
        200
    )
    return jsonify(response_data)


@app.errorhandler(400)
def bad_request(e):
    response_data = create_response_error(
        'BadRequest',
        'Bad request',
        400
    )
    return jsonify(response_data), response_data['status_code']


@app.errorhandler(403)
def forbidden(e):
    response_data = create_response_error(
        'Forbidden',
        'Forbidden',
        403
    )
    return jsonify(response_data), response_data['status_code']


@app.errorhandler(404)
def page_not_found(e):
    response_data = create_response_error(
        'PageNotFound',
        'Sorry, nothing at this URL',
        404
    )
    return jsonify(response_data), response_data['status_code']


@app.errorhandler(405)
def method_not_allowed(e):
    response_data = create_response_error(
        'MethodNotAllowed',
        'The method is not allowed for the requested URL',
        405
    )
    return jsonify(response_data), response_data['status_code']


@app.errorhandler(500)
def internal_server_error(e):
    response_data = create_response_error(
        'InternalServerError',
        'The server could not fulfill the request',
        500
    )
    return jsonify(response_data), response_data['status_code']

@app.route('/login/facebook', methods=['POST'])
@cross_origin(headers=['Content-Type', 'Authorization', 'Accept'])
def login_facebook():
    email = request.json.get('email')
    password = request.json.get('password')

    user = User.create(email, password)
    user.save()


@app.route('/users/location', methods=['POST'])
@cross_origin(headers=['Content-Type', 'Authorization', 'Accept'])
@login_required
def update_user_location():
    lat = request.json.get('lat')
    lon = request.json.get('lon')
    user_id = g.user.id

    User.update(user_id, lat, lon)


@app.route('/groups/<group_id>/locations')
@cross_origin(headers=['Content-Type', 'Authorization', 'Accept'])
@login_required
def get_friend_locations(group_id):
    group = Group.get_by_id(group_id)

    ret = []

    for friend_id in group.users:
        ret.extend([User.get_by_id(friend_id).to_dict()])

    response_data = create_response_data(
        {'friends': ret},
        200
    )
    return jsonify(response_data), response_data['status_code']


@app.route('/groups/<group_id>/add', methods=['POST'])
@cross_origin(headers=['Content-Type', 'Authorization', 'Accept'])
@login_required
def add_member_to_group(group_id):
    group = Group.get_by_id(group_id)
    user_id = request.json.get('user_id')

    if user_id is None:
        user_email = request.json.get('email')
        if user_email is None:
            raise Exception
        else:
            user = User.get_by_email(user_email)
            Group.add_member(group.id, user.id)
    else:
        Group.add_member(group.id, user_id)

@app.route('/groups', methods=['POST'])
@cross_origin(headers=['Content-Type', 'Authorization', 'Accept'])
@login_required
def create_group():
    group_id = request.json.get('group_id')
    name = request.json.get('name')

    group = Group.create(group_id=group_id,
                         creator=g.user.id,
                         name=name)

    group.save()

if __name__ == '__main__':
    app.run()