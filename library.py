from werkzeug import url_decode
from flask import Flask, session, render_template, request, redirect, url_for, flash
from time import gmtime, strftime
#from flask.ext.gzip import Gzip
import sqlite3 as lite
import json
import md5

#import pprint
#import sys

app = Flask(__name__, static_folder='static', static_url_path='')

class MethodRewriteMiddleware(object):
    """Middleware for HTTP method rewriting.

    Snippet: http://flask.pocoo.org/snippets/38/
    """

    def __init__(self, app):
        self.app = app      

    def __call__(self, environ, start_response):
        if 'METHOD_OVERRIDE' in environ.get('QUERY_STRING', ''):
            args = url_decode(environ['QUERY_STRING'])
            method = args.get('__METHOD_OVERRIDE__')
            if method:
                method = method.encode('ascii', 'replace')
                environ['REQUEST_METHOD'] = method
        return self.app(environ, start_response)


class Poll(object):

    def __init__(self, id = None, name = None):
        self.id = id
        self.name = name


app = Flask(__name__)
#gzip = Gzip(app)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'globocom_desafio'
app.wsgi_app = MethodRewriteMiddleware(app.wsgi_app)

def connect_db(database_name='poll.db'):
    return lite.connect(database_name)

def query_db(query, args=(), one=False):
    cur = connect_db().cursor()
    cur.execute(query, args)
    r = [dict((cur.description[i][0], value) \
               for i, value in enumerate(row)) for row in cur.fetchall()]
    cur.connection.close()
    return (r[0] if r else None) if one else r

@app.route('/')
def home():
    brothers = query_db("SELECT * FROM brothers",one=False)
    
    return render_template('home.html', brothers=brothers)

@app.route('/poll_result', methods=['GET','POST'])
def poll_result():
    query = "SELECT b.* FROM brothers as b"
    brothers = query_db(query,one=False);  

    if request.method == 'POST':
        oldVotos = int(request.form.get('votos')) + 1
        update_poll( request.form.get('brother'), oldVotos )

    return render_template('poll_result.html', brothers=brothers)

@app.route('/update_poll')
def update_poll( brotherId, oldVotos ):
    conn = lite.connect('poll.db')
    #try:
    conn.execute("UPDATE brothers SET votos=? WHERE id = ?", (oldVotos,brotherId) );   
    conn.commit()
    #except Exception:
    #    pass
    
def random_string():
    return strftime("%Y_%m_%d_%H_%M_%S", gmtime()) + md5.new(app.config['SECRET_KEY']).hexdigest()


@app.before_request
def csrf_protect():
    if request.method == "POST":
        token = session.pop('_csrf_token', None)
        if not token or token != request.form.get('_csrf_token'):
            abort(403)

def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = random_string()
    return session['_csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token



if __name__ == '__main__':
    app.run()