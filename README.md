### Public Prize

#### Setting up a dev environment (Fedora/CentOS)

Assumes you are running on a fresh Fedora:

##### Initialize postgres

```bash
su -
yum install -y postgresql-devel postgresql-server
postgresql-setup initdb
perl -pi.bak -e 's{\b(peer|ident)$}{password}' /var/lib/pgsql/data/pg_hba.conf
systemctl restart postgresql
echo "ALTER USER postgres PASSWORD 'postpass'" | su - postgres -c 'psql template1'
EOF
```

Perhaps need this for hostssl, but then you need to generate a key (not shown):


```bash
patch /var/lib/pgsql/data/postgresql.conf <<'EOF'
83,84c83,84
< #ssl = off                # (change requires restart)
< #ssl_ciphers = 'DEFAULT:!LOW:!EXP:!MD5:@STRENGTH' # allowed SSL ciphers
---
> ssl = on              # (change requires restart)
> ssl_ciphers = 'DHE-RSA-AES256-SHA:AES256-SHA:DHE-RSA-AES128-SHA:EDH-RSA-DES-CBC3-SHA:RC4-SHA:HIGH:!ADH'   # allowed SSL ciphers
519c519
< #client_encoding = sql_ascii      # actually, defaults to database
---
> client_encoding = 'UTF8'      # actually, defaults to database
```

##### Install home-env

https://github.com/biviosoftware/home-env

```bash
curl -s -L https://raw.githubusercontent.com/biviosoftware/home-env/master/install.sh | bash
```

Exit your shell and restart.

##### Install Python and publicprize env:

```bash
cd ~/src/biviosoftware
gcl publicprize
cd publicprize
bivio_pyenv_3
bivio_pyenv_local
```

This will create an "editable version" of this repository with pip so
that pytest can find the files.

#### Create test db

Run this to create a test db:

```bash
cd ~/src/biviosoftware/publicprize
python manage.py create_test_db
```

Subsequent runs of this command will produce
`role "ppuser" already exists`, which you can ignore.

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


##### Fedora

Set up in Fedora container (already setup for Python):

```bash
yum install -y postgresql-server postgresql-devel
postgresql-setup initdb
cat > /var/lib/pgsql/data/pg_hba.conf <<'EOF'
# TYPE  DATABASE    USER        CIDR-ADDRESS          METHOD
local   all         all                               trust
hostssl all         all         0.0.0.0/0             password
hostssl all         all         ::/0                  password
EOF
systemctl enable postgresql
systemctl start postgresql
```

Also needed:

```bash
sudo yum install -y libffi-devel
```
