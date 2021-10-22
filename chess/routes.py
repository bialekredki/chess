from datetime import datetime
from re import S
from flask.helpers import flash
from flask.json import jsonify
from flask_login.utils import login_required
from chess import app, db, socketio, mail
from flask import render_template, redirect, url_for, request
from chess.AI import AI_INTEGRATIONS_NAMES_LIST, StupidAI, get_ai
from chess.forms import ForgotPasswordForm, LoginForm, RegisterForm
from chess.game import MovesOrdering
from chess.game_options import GameFormat, GameOption
from chess.models import BlogPost, BlogPostComment, Message, RecoveryTry, User, Game
import flask_mail
from flask_login import current_user, login_user, logout_user
from chess.emailtoken import confirm_email_token, confrim_recovery_token, generate_email_token, generate_recovery_token
from chess.utils import round_datetime
from sqlalchemy import or_
from flask_socketio import SocketIO,send,emit
from PIL import Image
import json
from fuzzywuzzy import fuzz
import os.path
from chess.mail import send_mail



@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Home')

@app.route('/search_user', methods=['GET', 'POST'])
def search_user():
    data = request.form.get('data')
    records = int(request.form.get('records'))
    if records is None:
        records = 5
    all_users = User.query.all()
    result = list()
    min = 0
    for user in all_users:
        username = user.username
        ratio = fuzz.ratio(data.lower(), username.lower())
        if ratio < 60:
            continue
        if len(result) < records:
            result.append({'user':username, 'ratio':ratio})
            result.sort(reverse=True, key=lambda obj : obj['ratio'])
        elif result.at(-1)['ratio'] < ratio:
            result[len(result)-1] = {'user':user, ratio:ratio}
    return jsonify({'data': result})


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
    friends_posts=list()
    top_posts = BlogPost.query.order_by(BlogPost.upvotes.desc()).limit(5).all()
    latest_posts = BlogPost.query.order_by(BlogPost.timestamp_creation.desc()).limit(5).all()
    for friend in current_user.friends:
        for post in BlogPost.query.filter_by(user_id=friend.id).all():
            friends_posts.append(post)
    posts='test'
    return render_template('blog.html', posts=posts,friends_posts=friends_posts, top_posts=top_posts, latest_posts=latest_posts, title='Blog')

@app.route('/blog/post', methods=['POST'])
@login_required
def post_blog():
    for k,v in request.form.items():
        print(f'k:{k}\nv:{v}')
    post = BlogPost(subject=request.form['subject'], content=request.form['content'], user_id=current_user.id)
    db.session.add(post)
    db.session.commit()
    return redirect(url_for('blog'))

@app.route('/blog/<postid>')
@login_required
def see_post(postid):
    print(current_user.is_liking(BlogPost.query.filter_by(id=postid).first()))
    post:BlogPost = BlogPost.query.filter_by(id=postid).first_or_404()
    post.comments.sort(key=lambda x: x.timestamp_creation,reverse=True)
    for c in post.comments:
        print(c.timestamp_creation)
    print(post.comments)
    return render_template('post.html', post=post, title=f'Blog - {post.subject}')

@app.route('/blog/<postid>/upvote', methods=['POST'])
@login_required
def like_post(postid):
    post = BlogPost.query.filter_by(id=postid).first_or_404()
    print(post.liked_by.all())
    print(post.is_liked_by(current_user))
    if post.like(current_user):
        post.upvotes += 1
    db.session.commit()
    return render_template('post.html', post=post, title=f'Blog - {post.subject}')

@app.route('/blog/<postid>/downvote', methods=['POST'])
@login_required
def dislike_post(postid):
    post = BlogPost.query.filter_by(id=postid).first_or_404()
    print(post.liked_by.all())
    print(post.is_liked_by(current_user))
    if post.dislike(current_user):
        post.upvotes -= 1
    db.session.commit()
    return render_template('post.html', post=post, title=f'Blog - {post.subject}')

@app.route('/blog/<postid>/comment', methods=['POST'])
@login_required
def comment_post(postid):
    post = BlogPost.query.filter_by(id=postid).first_or_404()
    try:
        comment = BlogPostComment(content=request.form['content'], user_id=current_user.id, post_id=postid)
    except:
        return redirect(url_for('something_went_wrong'))
    db.session.add(comment)
    db.session.commit()
    return render_template('post.html', post=post, title=f'Blog - {post.subject}')

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
        token = generate_email_token(user.email)
        url = url_for('confirm_email', token=token, _external=True)
        subject = 'Notchess - Confirm your account!'
        send_mail(subject, user.email, url, 'mail/confirm_mail.html')
        login_user(user)
        return  redirect(url_for('index'))
    return render_template('register.html', title='Register', form=form)

@app.route('/forgot_password', methods=['GET','POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        recovery_try = RecoveryTry(user_id=User.query.filter_by(email=form.email.data).first().id, ipaddr=request.remote_addr)
        token = generate_recovery_token(email=form.email.data, ipaddr=request.remote_addr, id=recovery_try.id)
        send_mail('Notchess - Recover your password', form.email.data, url_for('reset_password', token=token, _external=True), 'mail/email_reset_password.html')
    return render_template('forgot_password.html',form=form, title='Password recovery')

@app.route('/reset/<token>', methods=['GET','POST'])
def reset_password(token):
    try:
        email, ipaddr, id = confrim_recovery_token(token)
    except:
        flash('The recovery link is invalid or has expired', 'danger')
    recovery_try = RecoveryTry.query.filter_by(id=id).first_or_404()
    print(ipaddr)
    if recovery_try.is_confirmed:
        flash('You have already recovered your password', 'info')
    else:
        recovery_try.is_confirmed = True
        db.session.commit()
        login_user(User.query.filter_by(email=email).first_or_404())
        return redirect(url_for('restore_password'))
    return redirect(url_for('index'), title='Reset password')

@app.route('/confirm/<token>')
def confirm_email(token):
    print(token)
    try:
        email = confirm_email_token(token)
    except:
        flash('The confirmation link is invalid or has expired', 'danger')
    print(email)
    user = User.query.filter_by(email=email).first_or_404()
    print(user)
    if user.is_confirmed:
        flash('Account already confirmed. Congrats!', 'success')
    else:
        user.is_confirmed = True
        db.session.commit()
        flash('You have successfully confirmed your account!', 'success')
    return redirect(url_for('index'))


@app.route('/me/<username>', methods=['GET', 'POST'])
@login_required
def user(username:User):
    user = User.query.filter_by(username=username).first_or_404()
    posts = BlogPost.query.filter_by(author=user)
    games = Game.query.filter(or_(Game.host==user, Game.guest==user)).order_by(Game.timestamp.desc()).limit(10).all()
    time_since = round_datetime(datetime.utcnow() - user.get_creation_date())
    return render_template('user.html', user=user, posts=posts, time_since=time_since,games=games)

@app.route('/me/<username>/games', methods=['GET'])
@login_required
def user_games(username:User):
    pass

@app.route('/me/add_friend', methods=['GET', 'POST'])
@login_required
def add_friend():
    sender = User.query.get(request.form.get('sender'))
    receiver = User.query.get(request.form.get('receiver'))
    sender.add_friend(receiver)
    return ('', 200)

@app.route('/me/remove_friend', methods=['GET', 'POST'])
@login_required
def remove_friend():
    sender = User.query.get(request.form.get('sender'))
    receiver = User.query.get(request.form.get('receiver'))
    sender.remove_friend(receiver)
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

@app.route('/api/play/ai_options', methods=['GET'])
@login_required
def play_api_get_ai():
    return jsonify({'ai_names':AI_INTEGRATIONS_NAMES_LIST, 'options':GameOption.ai_options()})

@app.route('/api/play/human_options', methods=['GET'])
@login_required
def play_api_get_human():
    return jsonify({'options':GameOption.human_options(), 'time_formats':GameFormat.all()})


@app.route('/play/<id>')
@login_required
def game(id):
    return render_template('game.html', game=Game.query.filter_by(id=id).first_or_404())

@socketio.on('message')
def message_handler(data):
    send(data)

@app.route('/play/new', methods=['GET', 'POST'])
@login_required
def create_game(guest_id:int=None,type:int=0):
    if guest_id is None and request.args.get('guest_id'):
        guest_id = int(request.args.get('guest_id'))
    if guest_id is None: return # look for a player
    print('New game')
    try:
        if guest_id == -1: 
            g = Game(current_user.id, guest_id, AI='Stupid')
            print(g.AI)
        else: 
            g = Game(current_user.id, guest_id)
            print('no ai')
    except:
        app.logger.error("%s submitted a move without permission[guest]", current_user.username,exc_info=True)
        return redirect(url_for('index'))
    db.session.add(g)
    db.session.commit()
    return redirect(url_for(f'game', id=g.id))

@socketio.on('getgame')
def set_game(js,methods='GET'):
    game:Game = Game.query.filter_by(id=js['id']).first()
    tiles = list()
    for r,row in enumerate(game.rows):
        tiles.append([tile.jsonify() for tile in row.tiles])
    print(tiles)
    socketio.emit('setgame',{'tiles':tiles})

@socketio.on('getcolour')
def set_colour(js,methods='GET'):
    game:Game = Game.query.filter_by(id=js['id']).first()
    user:User = User.query.filter_by(id=js['player_id']).first()
    if not user.is_in_game(game): return
    socketio.emit('setcolour',{'colour':user.plays_as_white(game)})

@socketio.on('getpossiblemoves')
def get_possible_moves(js, methods=['GET']):
    id = js['gameid']
    game:Game = Game.query.filter_by(id=id).first()
    if not game.compare_with_js(js['game']['tiles']):
        app.logger.info("Comparison failed")
        return  
    if current_user.id != game.host_id and current_user.id != game.guest_id:
        return #TODO: Handle discrepancies on server-client
    socketio.emit('setpossiblemoves', {'moves': game.get_moves(js['from']), 'to':current_user.id})

@socketio.on('confirmmove')
def confirm_move(js, methods='GET'):
    app.logger.info("Move request\n%s", str(js))
    id = js['gameid']
    game:Game = Game.query.filter_by(id=id).first()
    print('FUCKING TURN', game.turn)
    if not game.compare_with_js(js['game']['tiles']):
        app.logger.info("Comparison failed")
        return
    if not current_user.is_in_game(game):
        app.logger.info("%s submitted a move without permission[guest]", current_user.username)
        return
    if current_user.plays_as_white(game) and not game.at(js['from']).colour:
        app.logger.info("%s submitted a move without permission[black]", current_user.username)
        return
    if current_user.plays_as_black(game) and game.at(js['from']).colour:
        app.logger.info("%s submitted a move without permission[white]", current_user.username)
        return
    if current_user.plays_as_black(game) and game.turn:
        app.logger.info("%s submitted a move outside his turn[white]", current_user.username)
        return
    if current_user.plays_as_white(game) and not game.turn:
        app.logger.info("%s submitted a move outside his turn[black]", current_user.username)
        return
    possible_moves = game.get_all_moves(order_by=MovesOrdering.BY_SOURCE)
    if tuple(js['from']) not in possible_moves.keys() or js['to'] not in possible_moves[tuple(js['from'])]:
        app.logger.info('%s submitted impossible move', current_user.username)
        return
    game.move(js['from'], js['to'])
    game.turn = not game.turn
    game.set_check(game.turn)
    print('Turn on players mOVE', game.turn)
    socketio.emit('move', {'from': js['from'], 'to': js['to']}, broadcast=True)
    if game.AI is not None and current_user.plays_as_white(game) != game.turn:
        possible_moves = game.get_all_moves(colour=not game.at(js['to']).colour)
        move = get_ai(game.AI).make_stupid_move(possible_moves)
        game.move(move[0], move[1])
        game.turn = not game.turn
        print('Turn on AI mOVE', game.turn)
        socketio.emit('move', {'from': move[0], 'to': move[1]}, broadcast=True)
    db.session.commit()
    
    