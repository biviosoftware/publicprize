import unittest
from flask import Flask, request
app = Flask(__name__)

@app.route('/')
def _route_slash():
    return 'root'

@app.route('/<path>')
def _route_path(path):
    return 'path'

@app.route('/<first>/<rest>')
def _route_first_rest(first, rest):
    return 'first rest'

class Test(unittest.TestCase):
    
    def setUp(self):
        global app
        self.client = app.test_client()

    def test_route(self):

        def t(uri, expect):
            rv = self.client.get(uri)
            body = rv.data.decode('utf-8');
            assert expect == body, 'expect={} but got={}'.format(expect, body)

        t('/', 'root')
        t('/x', 'path')
        t('/x/y', 'first rest')
        t('//x', 'first rest')

if __name__ == '__main__':
    unittest.main()
