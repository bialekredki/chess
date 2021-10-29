from datetime import datetime
from re import S
import re
from flask.helpers import flash
from flask.json import jsonify
from flask_login.utils import login_required
from sqlalchemy.sql.elements import conv
from chess import app, db, socketio, mail, celery
from flask import render_template, redirect, url_for, request
from chess.AI import AI_INTEGRATIONS_NAMES_LIST, StockfishIntegrationAI, StupidAI, get_ai
from chess.forms import ForgotPasswordForm, LoginForm, RegisterForm
from chess.game import Move, MovesOrdering, PieceType
from chess.game_options import GameFormat, GameOption
from chess.game import Game as ChessGame
from chess.models import BlogPost, BlogPostComment, GameState, MatchmakerRequest, Message, RecoveryTry, User, Game
import flask_mail
from flask_login import current_user, login_user, logout_user
from chess.emailtoken import confirm_email_token, confrim_recovery_token, generate_email_token, generate_recovery_token, generate_game_invitation_token, confirm_game_invitation_token
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

@app.route('/messages', methods=['GET', "POST"])
def messages():
    return render_template('messages.html', title='Messages')

@app.route('/api/user/messages', methods=['GET'])
def api_messages():
    messages = list()
    conversations = dict()
    all = {'sent':current_user.sent, 'received':current_user.received}
    for key,ms in all.items():
        if request.args.get(key) is None or not request.args.get(key):continue
        for m in ms:
            if key == 'received' and not m.receiver_seen:
                m.mark_as_seen()
                print(m.receiver_seen)
            if key == 'sent':
                messages.append(m)
            if (key == 'received' and m.receiver_seen) and request.args.get('seen', False):
                messages.append(m)
            if (key == 'received' and not m.receiver_seen) and request.args.get('unseen', False):
                messages.append(m)

    messages.sort(key=lambda x:x.timestamp_creation,reverse=False)
    if request.args.get('conversation'):
        for m in messages:
            if request.args.get('users[]') is not None:
                for user in request.args.getlist('users[]'):
                    u:User = User.query.filter_by(username=user).first()
                    if user not in conversations: conversations[user] = list()
                    if m.sender_id == u.id or m.receiver_id == u.id:
                        conversations[user].append(m.jsonify())
                        break
            else:
                id = m.sender_id if m.receiver_id == current_user.id else m.receiver_id
                u:User = User.query.filter_by(id=id).first()
                if u.username not in conversations: conversations[u.username] = list()
                conversations[u.username].append(m.jsonify())
    if request.args.get('count'):return jsonify({'len':len(messages)})
    if request.args.get('conversation'): return jsonify(conversations)
    return jsonify({'messages':messages})

@app.route('/api/user/messages', methods=['POST'])
def api_messages_send():
    m:Message = Message(sender_id = current_user.id, receiver_id = User.query.filter_by(username=request.form['receiver']).first().id, content=request.form['content'])
    db.session.add(m)
    db.session.commit()
    socketio.emit('send_message', {'sender': current_user.username}, namespace=f"/messages-{User.query.filter_by(username=request.form['receiver']).first().id}")
    return ('', 200)


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
    games = Game.query.filter(or_(Game.host==user, Game.guest==user)).order_by(Game.timestamp_creation.desc()).limit(10).all()
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

@app.route('/api/play/game_setup', methods=['GET'])
@login_required
def api_play_game_setup():
    result = dict()
    app.logger.info("%s [API] %s %s", current_user.username, __name__, request.args)
    if request.args.get('ai'):
        result['AI'] = list()
        for name in AI_INTEGRATIONS_NAMES_LIST:
            result['AI'].append({'id':name, 'name':name, 'type':'btn'})
    
    if request.args.get('friends'):
        result['Friends'] = list()
        for friend in current_user.friends:
            result['Friends'].append({'id': friend.username, 'name':render_template('user/user_span.html', user=friend), 'type':'btn'})

    if request.args.get('time'):
        result['Time Control'] = GameFormat.all()

    if request.args.get('options[]'):
        result['Options'] = list()
        for option in request.args.getlist('options[]'):
            result['Options'].append(GameOption.getbyname(option).value)
    return jsonify(result)




@app.route('/play/<id>')
@login_required
def game(id):
    return render_template('game.html', game=Game.query.filter_by(id=id).first_or_404())

@socketio.on('message')
def message_handler(data):
    send(data)

@app.route('/play/new', methods=['POST'])
@login_required
def create_game(guest_id:int=None,type:int=0):
    app.logger.error("%s [GAME] starts a new game with %s", current_user.username, request.form)
    if request.form.get('AI'):
        guest_id = -1
        if request.form.get('bar',False) == 'true': bar = True
        else: bar = False
        g = Game(host_id=current_user.id, guest_id=guest_id, AI=request.form.get('AI'), show_eval_bar=bar)
        g.game_state.append(GameState())
        db.session.add(g)
        print(g)
        db.session.commit()
        return url_for(f'game', id=g.id)
    if request.form.get('Friends') is not None:
        guest:User = User.query.filter_by(username=request.form.get('Friends')).first()
        guest_id = guest.id
        token = generate_game_invitation_token(current_user.id, guest_id)
        message:Message = Message(receiver_id=guest_id, sender_id=current_user.id, content=f"Invites you to <a href='{url_for('create_game_invitation', token=token)}'>game</a>")
        socketio.emit('send_message', {'sender': current_user.username}, namespace=f'/messages-{guest_id}')
        db.session.add(message)
        db.session.commit()
        return ('', 200)
    if guest_id is None: return ('', 200)

@app.route('/play/matchmaker/<id>', methods=['GET','POST'])
@login_required
def play_matchmaker(id):
    user:User = User.query.filter_by(id=id).first_or_404()
    if user.mm_request is None:
        user.mm_request = MatchmakerRequest()
        db.session.add(user.mm_request)
        db.session.commit()
    while True:
        requests = MatchmakerRequest.query.all()
        for request in requests:
            print(request)
            print(user.mm_request.fulfills_conditions(request))
    return ('', 200)


@app.route('/play/new/<token>', methods=['GET','POST'])
@login_required
def create_game_invitation(token):
    print(token)
    try:
        host_id, guest_id = confirm_game_invitation_token(token)
    except:
        return redirect(url_for('index'))

    if guest_id != current_user.id: return redirect(url_for('index'))
    game:Game = Game(host_id=host_id,guest_id=guest_id)
    gs = GameState()
    db.session.add(gs)
    db.session.add(game)
    game.game_state.append(gs)
    db.session.commit()
    socketio.emit('game_ready', {'url': url_for('game', id=game.id)} , namepsace=f'/messages-{host_id}')
    return redirect(url_for('game', id=game.id))

@app.route('/api/game/history/<id>', methods=['GET'])
@login_required
def api_game_history():
    game:Game = Game.query.filter_by(id=request.args.get['id']).first_or_404()
    if request.args.get('all'): return ('', 200)
    return 

@socketio.on('getgame')
def set_game(js,methods='GET'):
    game:Game = Game.query.filter_by(id=js['id']).first()
    print(game.game_state[-1].to_list())
    print(game.game_state[-1].to_fen())
    if game.show_eval_bar:
        eval = StockfishIntegrationAI(game.get_current_state().to_fen(), 15).engine.get_evaluation()
        eval = eval['value']
        print(eval)
        if eval < -2000: eval = -2000
        if eval > 2000: eval = 2000
        print(eval)
        eval = ((eval + 2000)/(4000))*100
        print(eval)
        socketio.emit('setgame', {'tiles': game.game_state[-1].to_list(), 'eval': eval}, namespace=f'/game-{game.id}')
    else:
        socketio.emit('setgame', {'tiles': game.game_state[-1].to_list()}, namespace=f'/game-{game.id}')

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
    print(game.get_current_state().to_fen())
    chess_game = ChessGame(game.game_state[-1].to_list(), game.game_state[-1].to_fen())
    if current_user.id != game.host_id and current_user.id != game.guest_id:
        return #TODO: Handle discrepancies on server-client
    print([move.jsonify()['to'] for move in chess_game.get_moves(js['from'])])
    socketio.emit('setpossiblemoves', {'moves': [move.jsonify()['to'] for move in chess_game.get_moves(js['from'])], 'to':current_user.id}, namespace=f'/game-{game.id}')
    

@socketio.on('confirmmove')
def confirm_move(js, methods='GET'):
    app.logger.info("Move request\n%s", str(js))
    id = js['gameid']
    game:Game = Game.query.filter_by(id=id).first()
    current_state = game.get_current_state()
    print(current_state.to_fen())
    if not current_user.is_in_game(game):
        app.logger.info("%s submitted a move without permission[guest]", current_user.username)
        return
    if current_user.plays_as_black(game) and current_state.is_white_turn():
        app.logger.info("%s submitted a move outside his turn[white]", current_user.username)
        return
    if current_user.plays_as_white(game) and current_state.is_black_turn():
        app.logger.info("%s submitted a move outside his turn[black]", current_user.username)
        return
    sf = StockfishIntegrationAI(current_state.to_fen())
    print(current_state.to_fen())
    print(sf.engine.get_board_visual())
    move = Move(js['from'], js['to'])
    move = move.algebraic()
    cg = ChessGame(current_state.to_list(), current_state.to_fen())
    if js['to'][0] == 7 and cg.at(js['from']).piece == PieceType.PAWN.value and cg.at(js['from']).colour or js['to'][0] == 0 and cg.at(js['from']).piece == PieceType.PAWN.value and not cg.at(js['from']).colour:
        move += 'Q'
    if not sf.is_possible(move):
        app.logger.info('%s submitted impossible move', current_user.username)
        return
    print(sf.engine.get_board_visual())
    fen = sf.move(move)
    print(sf.engine.get_board_visual())
    new_state = GameState()
    game.game_state.append(new_state)
    new_state.set(fen)
    print('MOVE PLAYER', new_state.to_fen())
    if game.AI is not None and ((current_user.plays_as_white(game) and new_state.is_black_turn()) or (current_user.plays_as_black(game) and new_state.is_white_turn())):
        ai = get_ai(game.AI, new_state.to_fen())
        move = ai.best_move()
        fen = ai.move(move)
        new_state = GameState()
        new_state.set(fen)
        game.game_state.append(new_state)
        print(new_state.to_fen())
        move = Move.from_algebraic(move)
        if game.show_eval_bar:
            eval = StockfishIntegrationAI(game.get_current_state().to_fen(), 15).engine.get_evaluation()
            eval = eval['value']
            print(eval)
            if eval < -2000: eval = -2000
            if eval > 2000: eval = 2000
            print(eval)
            eval = ((eval + 2000)/(4000))*100
            print(eval)
            socketio.emit('setgame', {'tiles': game.game_state[-1].to_list(), 'eval': eval}, namespace=f'/game-{game.id}')
        else:
            socketio.emit('setgame', {'tiles': game.game_state[-1].to_list()}, namespace=f'/game-{game.id}')
            print('Second')
    else:
            if game.show_eval_bar:
                eval = StockfishIntegrationAI(game.get_current_state().to_fen(), 15).engine.get_evaluation()
                eval = eval['value']
                print(eval)
                if eval < -2000: eval = -2000
                if eval > 2000: eval = 2000
                print(eval)
                eval = ((eval + 2000)/(4000))*100
                print(eval)
                socketio.emit('setgame', {'tiles': game.game_state[-1].to_list(), 'eval': eval}, namespace=f'/game-{game.id}')
            else:
                socketio.emit('setgame', {'tiles': game.game_state[-1].to_list()}, namespace=f'/game-{game.id}')
    db.session.commit()
    
    