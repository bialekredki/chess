from chess.api import *

@auth.verify_password
def verify_password(username_token, password):
    user:User = User.verify_auth_token(username_token)
    if not user:
        user:User = User.query.filter_by(username=username_token).first()
        if not user or not user.check_password(password):
            return False
    g.user = user
    return True


@app.route('/api/auth', methods=['GET'])
@auth.login_required
def api_auth_token():
    token = g.user.generate_auth_token()
    return jsonify({ 'token': token.decode('ascii') })