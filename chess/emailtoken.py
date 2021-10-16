from datetime import datetime
from itsdangerous import URLSafeTimedSerializer, serializer

from chess import app, mail, db
from chess.models import Message, RecoveryTry,User

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