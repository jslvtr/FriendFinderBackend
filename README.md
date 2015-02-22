# FriendFinderBackend
Backend in Python and Flask for FriendFinder

## API Reference

### Users

#### POST `/users/register`

This registers you and logs you in. It will return an `access_token` which you need in further communication.
Please send me:

```
{
    "email": <valid_email>,
    "password": <sha1>
}
```

#### POST `/users/login`

This logs you in. It will return an `access_token` which you need in further communication.
Please send me:

```
{
    "email": <valid_email>,
    "password": <sha1>
}
```

#### POST `/users/location/`

Needs to be logged in. Send as `Authorization header`: `FFINDER <access_token>`.
This updates the current user's location with the data in the JSON payload.
Please send me:

```
{
    "lat": <float>,
    "lon": <float>
}
```

Instead of `email` you can send `id`.

### Groups

#### GET `/groups/<group_id>/locations`

Needs to be logged in. Send as `Authorization header`: `FFINDER <access_token>`.
This returns the users in a group and their locations.
You will get:

```
[
    {
    "id": <string>,
    "location": {
        "lat": <float>,
        "lon": <float>
        }
    "email": <valid_email>
    },
    ...
]
```

#### POST `/groups/<group_id>/add`

Needs to be logged in. Send as `Authorization header`: `FFINDER <access_token>`.
This lets you add a user with a given e-mail address to the group.
Send me:

```
{
    "email": <valid_email>
}
```

You can send me a `user_id` instead of `email`.

#### POST `/groups`

Needs to be logged in. Send as `Authorization header`: `FFINDER <access_token>`.
This creates a new group.
Send me:

```
{
    "group_id": <string>,
    "name": <string>
}
```

#### GET `/groups`

Needs to be logged in. Send as `Authorization header`: `FFINDER <access_token>`.
This gets the current user's groups

You'll receive:

```
[
    {
    "id": <string>,
    "name": <string>,
    "users": [
            <user_id1>,
            <user_id2>,
            ...
        ]
    },
    ...
]
```