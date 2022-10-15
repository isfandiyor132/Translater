import sqlite3
import googletrans
from config import *
from functools import wraps
from googletrans import Translator
from authlib.integrations.flask_client import OAuth
from flask import Flask, redirect, url_for, session, render_template, request

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='static',)
oauth = OAuth(app)
translator = Translator()

connect = sqlite3.connect('clients.db' , check_same_thread=False)
cursor = connect.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS users( id TEXT, name TEXT, words_max INTEGER, words_used INTEGER )""")

app.config['SECRET_KEY'] = SECRET_KEY
app.config['GOOGLE_CLIENT_ID'] = CLIENT_ID
app.config['GOOGLE_CLIENT_SECRET'] = CLIENT_SECRET

google = oauth.register(
    name = 'google',
    client_id = app.config["GOOGLE_CLIENT_ID"],
    client_secret = app.config["GOOGLE_CLIENT_SECRET"],
    access_token_url = 'https://accounts.google.com/o/oauth2/token',
    access_token_params = None,
    authorize_url = 'https://accounts.google.com/o/oauth2/auth',
    authorize_params = None,
    api_base_url = 'https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint = 'https://openidconnect.googleapis.com/v1/userinfo',
    client_kwargs = {'scope': "https://www.googleapis.com/auth/userinfo.profile"},
)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = dict(session).get('profile', None)
        if user:
            return f(*args, **kwargs)
        return render_template('index.html', languages=googletrans.LANGUAGES, user_data=None)
    return decorated_function

def get_data(user_id):
    cursor.execute(f"SELECT words_max, words_used FROM users WHERE id = '{user_id}'")
    data = cursor.fetchone()
    return data

@app.route('/')
@login_required
def main_page():
    user_data = dict(session)["profile"]
    words_info = get_data(user_data["id"])
    try:
        data = request.args['messages']
        return render_template('index.html', googletrans.LANGUAGES, result=data[1], origin=data[2], from_lang=data[3], to_lang=data[4], user_data=user_data, words_info=words_info)
    except:
        return render_template('index.html', languages=googletrans.LANGUAGES, user_data=user_data, words_info=words_info)

@app.route('/translate', methods=['GET', 'POST'])
@login_required
def translate_page():
    text = request.form['text']
    from_lang = request.form['from_lang']
    to_lang = request.form['to_lang']
    words = list(map(str, text.split(" ")))

    if from_lang != "DETECT LANGUAGE":
        result = translator.translate(text, src=from_lang, dest=to_lang)
    else:
        result = translator.translate(text, dest=to_lang)
    origin = result.origin
    result = result.text
    user_data = dict(session)["profile"]
    words_info = get_data(user_data["id"])
    cursor.execute(f'''UPDATE users SET words_used = '{words_info[1] + len(words)}' WHERE id = '{user_data["id"]}' ''')
    connect.commit()
    words_info = [words_info[0], words_info[1] + len(words)]
    data = [result, origin, from_lang, to_lang]
    return redirect(url_for('.main_page', messages=data))

@app.route('/login')
def login():
    google = oauth.create_client('google')
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/authorize')
def authorize():
    google = oauth.create_client('google')
    token = google.authorize_access_token()
    resp = google.get('userinfo')
    user_info = resp.json()
    user = oauth.google.userinfo()
    session['profile'] = user_info
    session.permanent = True

    user_data = dict(session)["profile"]
    cursor.execute(f'''SELECT id FROM users WHERE id = '{user_data["id"]}' ''')
    is_exist = cursor.fetchone()
    if is_exist is None:
        cursor.execute(f'INSERT INTO users(id, name, words_max, words_used) VALUES (?, ?, ?, ?)', (user_data["id"], user_data["name"], 10000, 0))
        connect.commit()
    return redirect('/')

@app.route('/logout')
def logout():
    for key in list(session.keys()):
        session.pop(key)
    return redirect('/')

app.run()