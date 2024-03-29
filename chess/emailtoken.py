from datetime import datetime
from itsdangerous import URLSafeTimedSerializer, URLSafeSerializer

from chess import app, mail, db
from chess.models import Message, RecoveryTry,User

def friendship_request_token(sender:User, receiver:User):
    serializer = URLSafeSerializer(app.config['SECRET_KEY'])
    return serializer.dumps({'sender': (sender.username, sender.id), 'receiver':(receiver.username, receiver.id)}, salt=app.config['SECURITY_PASSWORD_SALT'])

def get_friendship_request_token(token):
    serializer = URLSafeSerializer(app.config['SECRET_KEY'])
    try:
        users:dict = serializer.loads(token, salt=app.config['SECURITY_PASSWORD_SALT'])
    except:
        return False
    return users

def game_socket_token(game_id:int,user_id:int):
    serializer = URLSafeSerializer(app.config['SECRET_KEY'])
    return serializer.dumps((game_id, user_id), salt=app.config['SECURITY_PASSWORD_SALT'])

def get_game_socket_token(token):
    serializer = URLSafeSerializer(app.config['SECRET_KEY'])
    try:
        ids = serializer.loads(token, salt=app.config['SECURITY_PASSWORD_SALT'])
    except:
        return False
    return ids

def generate_email_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])

def confirm_email_token(token, expiration=36000):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token,salt=app.config['SECURITY_PASSWORD_SALT'], max_age=expiration)
    except:
        return False
    return email

def generate_recovery_token(email,ipaddr,id):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps([email, ipaddr, id], salt=app.config['SECURITY_PASSWORD_SALT'])

def confrim_recovery_token(token, expiration=36000):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email,ipaddr,id = serializer.loads(token,salt=app.config['SECURITY_PASSWORD_SALT'], max_age=expiration)
    except:
        return False
    return email,ipaddr,id

def generate_game_invitation_token(host_id, guest_id, options):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps([host_id, guest_id, options], salt=app.config['SECURITY_PASSWORD_SALT'])

def confirm_game_invitation_token(token, expiration=240):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        host_id, guest_id, options = serializer.loads(token,salt=app.config['SECURITY_PASSWORD_SALT'], max_age=expiration)
    except:
        return False
    return host_id, guest_id, options

def generate_matchmaking_token(user_id:int, options:dict):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps((user_id, options), salt=app.config['SECURITY_PASSWORD_SALT'])

def resolve_matchmaking_token(token):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        user_id, options = serializer.loads(token,salt=app.config['SECURITY_PASSWORD_SALT'])
    except:
        return False
    return user_id, options