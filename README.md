Public Prize
============

###### Setting up a dev environment.

First [install Python3 with pyenv](//github.com/biviosoftware/utilities/blob/master/Environment.md), then:

```bash
pip install -e .
```

This will create an "editable version" of this repository with pip so
that pytest can find the files.

To update `requirements.txt`, do:

pip freeze | grep -v -- '^-e ' > requirements.txt

###### Create test db

Run this to create a test db:

```bash
python manage.py create_test_db
```

Subsequent runs of this command will produce
`role "ppuser" already exists`, which you can ignore.

Postgresql should already be running.

You may need to run as root:

```bash
echo "ALTER USER postgres PASSWORD 'postpass';COMMIT" | su - postgres -c 'psql template1'
```

###### Environment Variables

Application secret values are controlled by the environment. Add the
items below to enable Facebook, Google and PayPal features. Test
applications for each service can be created on the respective
developer websites.

```bash
export FACEBOOK_APP_ID=...
export FACEBOOK_APP_SECRET=...
export GOOGLE_APP_ID=...
export GOOGLE_APP_SECRET=...
export PAYPAL_MODE=sandbox
export PAYPAL_CLIENT_ID=...
export PAYPAL_CLIENT_SECRET=...
```

###### Running Flask server

Starts the server from this directory:

```bash
python manage.py runserver -h 0.0.0.0 -p 8000
```

###### Logging in as a test user

You can avoid using the social network login by visiting the url:

http://localhost:8000/pub/new-test-user

Each time you visit the url above, a new user will be created and
logged in.

###### Running pytests

```bash
py.test
```

Run a single test:

```bash
py.test tests/test_debug.py
```

Run a single test function:

```bash
py.test tests/test_workflow.py -k test_submit_website_dev_entries
```

###### Travis

https://travis-ci.org/biviosoftware/publicprize

Click on this:

https://travis-ci.org/biviosoftware/publicprize/builds

Then the number of the build, e.g. 2 or 4, to see the build history

The control file is .travis.yml
