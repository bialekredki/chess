from datetime import datetime
from flask.helpers import flash
from flask_login.utils import login_required
from chess import app, db
from flask import render_template, redirect, url_for
from chess.forms import LoginForm, RegisterForm
from chess.models import BlogPost, User, Game
from flask_login import current_user, login_user, logout_user
from chess.utils import round_datetime
from sqlalchemy import or_



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

@app.route('/play', methods=['GET', 'POST'])
@login_required
def play():
    return render_template('play.html')