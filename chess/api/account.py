from chess.api import *

@app.route('/api/me/data', methods=['GET'])
@auth.login_required
def api_account_data():
    response_object = dict()
    user:User = g.user
    response_object['id'] =  user.id
    response_object['username'] = user.username
    response_object['private'] = user.private
    response_object['url'] = url_for('user', username=user.username)
    response_object['email'] = user.email
    if user.name is not None: response_object['name'] = user.name
    response_object['ranking'] = user.get_current_rating().jsonify()
    response_object['friends'] = [f.username for f in user.friends]
    response_object['games'] = list()
    for games in [user.hostgames, user.guestgames]:
        for game in games:
            response_object['games'].append(url_for('game_token', token=game_socket_token(game.id, user.id)))
    return (jsonify(response_object), 200)

@app.route('/api/me/email', methods=['GET'])
@auth.login_required
def api_account_email():
    return (g.user.email, 200)

@app.route('/api/me/theme', methods=['GET', 'POST'])
@auth.login_required
def api_account_theme():
    if request.method == 'POST':
        try:
            g.user.set_theme(request.form.get('theme'))
            return ('', 200) 
        except:
            return ('', 404)
    else:
        if request.args.get('verbose'): return (g.user.get_theme().jsonify(), 200)
        else: return (g.user.theme, 200)

@app.route('/api/me/private', methods=['GET', 'POST'])
@auth.login_required
def api_account_private():
    user:User = g.user
    if request.method == 'POST':
        try:
            private = request.form.get('private')
            if private is None: raise Exception()
            if type(private) is str: private = bool(private)
            user.set_private(private)
            return ('', 200) 
        except:
            return ('', 404)
    else:
        return (jsonify(user.private), 200)