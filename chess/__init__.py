from flask import Flask
import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from flask_socketio import SocketIO
from flask_mail import Mail

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'admin'
app.config['SECURITY_PASSWORD_SALT'] = 'stary_pijany'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or \
    'sqlite:///' + os.path.join(basedir, 'chess.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USE_TLS'] = False 
app.config['MAIL_PORT']=465
app.config['MAIL_USERNAME'] = os.environ['APP_MAIL_USERNAME']
app.config['MAIL_PASSWORD'] = os.environ['APP_MAIL_PASSWORD']
app.config['MAIL_DEFAULT_SENDER'] = 'oskarkorgul@gmail.com'
db = SQLAlchemy(app)
migrate = Migrate(app,db)
login = LoginManager(app)
login.login_view = 'login'
bootstrap = Bootstrap(app)
socketio = SocketIO(app)
mail = Mail(app)

if __name__ == '__main__':
    socketio.run(app, debug=True)

from chess import routes, models