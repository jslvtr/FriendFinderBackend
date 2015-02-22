# FriendFinderBackend
Backend in Python and Flask for FriendFinder

## API Reference

### Users

#### POST `/users/register`

Please send me:

```
{
    "email": <valid_email>,
    "password": <sha1>
}
```

#### POST `/users/login`

Please send me:

```
{
    "email": <valid_email>,
    "password": <sha1>
}
```

#### POST `/users/location/`

Please send me:

```
{
    "email": <valid_email>,
    "lat": <float>,
    "lon": <float>
}
```

Instead of `email` you can send `id`.

### Groups

#### GET `/groups/<group_id>/locations`

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

Send me:

```
{
    "email": <valid_email>
}
```

You can send me a `user_id` instead of `email`.

#### POST `/groups`

This creates a new group.
Send me:

```
{
    "group_id": <string>,
    "name": <string>
}
```

#### GET `/groups`

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