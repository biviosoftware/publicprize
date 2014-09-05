Public Prize
============

###### Setting up a dev environment.

First [install Python3 with pyenv](//github.com/biviosoftware/utilities/blob/master/Environment.md), then:

```
pip install `cat requirements.txt`
pip install -e .
```

This will create an "editable version" of this repository with pip so
that pytest can find the files.

###### Postgresql database

A postgresql server must be running with the utf8 character
encoding. The tail of the pg_hba.conf must be:

```
# TYPE  DATABASE    USER        CIDR-ADDRESS          METHOD

# "local" is for Unix domain socket connections only
local   all         all                               trust
# IPv4 local connections:
host    all         all         127.0.0.1/32          password
# IPv6 local connections:
host    all         all         ::1/128               password
```

###### Create test db

Run this to create a test db:

```
python manage.py create_test_db
```

Subsequent runs of this command will produce
`role "ppuser" already exists`, which you can ignore.

Postgresql should already be running.

###### Environment Variables

Application secret values are controlled by the environment. Add the
items below to enable Facebook and PayPal features. Test applications
for each service can be created on the respective developer websites.

```
export FACEBOOK_APP_ID=...
export FACEBOOK_APP_SECRET=...
export PAYPAL_MODE=sandbox
export PAYPAL_CLIENT_ID=...
export PAYPAL_CLIENT_SECRET=...
```

###### Running Flask server

Starts the server from this directory:

```
python manage.py runserver -h 0.0.0.0 -p 8000
```

###### Logging in as a test user

You can avoid using the social network login by visiting the url:

http://localhost:8000/pub/new-test-user

Each time you visit the url above, a new user will be created and
logged in.

###### Running pytests

```
py.test
```

