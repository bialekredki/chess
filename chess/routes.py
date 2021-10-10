from datetime import datetime
from flask.helpers import flash
from flask.json import jsonify
from flask_login.utils import login_required
from chess import app, db, socketio
from flask import render_template, redirect, url_for, request
from chess.forms import LoginForm, RegisterForm
from chess.models import BlogPost, User, Game
from flask_login import current_user, login_user, logout_user
from chess.utils import round_datetime
from sqlalchemy import or_
from flask_socketio import SocketIO,send,emit
from PIL import Image
import json
import os.path



@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Home')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        #flash(f'Login requested for user {form.username.data}, remember_me={form.remember_me.data}')
        return redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form)

@app.route('/blog')
@login_required
def blog():
    posts = BlogPost.query.all()
    return render_template('blog.html', posts=posts)

@app.route('/register', methods=['GET', "POST"])
def create_account():
    if current_user.is_authenticated:
            return redirect(url_for('index'))
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        return  redirect(url_for('index'))
    return render_template('register.html', title='Register', form=form)


@app.route('/me/<username>', methods=['GET', 'POST'])
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = BlogPost.query.filter_by(author=user)
    games = Game.query.filter(or_(Game.host==user, Game.guest==user))
    time_since = round_datetime(datetime.utcnow() - user.joined)
    return render_template('user.html', user=user, posts=posts, time_since=time_since,games=games)

@app.route('/me/add_friend', methods=['GET', 'POST'])
@login_required
def add_friend():
    print('Add friend')
    for k,v in request.form.items():
        print(f'{k}: {v}')
    sender = User.query.get(request.form.get('sender'))
    receiver = User.query.get(request.form.get('receiver'))
    sender.friends.append(receiver)
    receiver.friends.append(sender)
    db.session.commit()
    return ('', 200)

@app.route('/submit_image', methods=['POST', "GET"])
@login_required
def submit_image():
    for k,v in request.form.items():
        print(f'{k}: {v}')
    for k,v in request.files.items():
        print(f'{k}: {v}')
    image = request.files.get('image')
    ALLOWED_EXTENSIONS = ['jpg', 'png', 'jpeg']
    if image is None or image.filename == '' or '.' not in image.filename or image.filename.split('.', 1)[1].lower() not in ALLOWED_EXTENSIONS:
        return
    
    user = User.query.get(request.form.get('user_id'))
    user.has_avatar = True
    db.session.commit()
    im = Image.open(image)
    print(im)
    filename = f'{user.id}.png'
    im = im.resize((128,128))
    im.save(os.path.join(os.path.realpath('chess/static/img/avatar/'), filename))
    filename = f'{user.id}_mini.png'
    im = im.resize((32,32))
    im.save(os.path.join(os.path.realpath('chess/static/img/avatar/'), filename))
    im.close()
    #image.save(os.path.join(os.path.realpath('chess/static/img/avatar/'), filename))
    return ('', 204)

@app.route('/play', methods=['GET', 'POST'])
@login_required
def play():
    return render_template('play.html')


@app.route('/play/<id>')
@login_required
def game(id):
    return render_template('game.html')

@socketio.on('message')
def message_handler(data):
    send(data)

@app.route('/play/new', methods=['GET', 'POST'])
@login_required
def create_game(host,guest:User=None,type:int=0):
    if guest is None: return # look for a player
    g = Game(host,guest)
    if guest != -1:
        db.session.add(g)
        db.session.commit(g)
    return redirect(f'/play/{g.id}')