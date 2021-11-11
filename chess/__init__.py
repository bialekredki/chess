from flask import Flask
import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from flask_socketio import SocketIO
from flask_mail import Mail
from logging.config import dictConfig
from celery import Celery

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

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


celery = Celery(app.name, backend='rpc://')
celery.conf.update(app.config)
db = SQLAlchemy(app)
migrate = Migrate(app,db, render_as_batch=True)
login = LoginManager(app)
login.login_view = 'login'
bootstrap = Bootstrap(app)
socketio = SocketIO(app)
mail = Mail(app)
x = None
if __name__ == '__main__':
    socketio.run(app, debug=True)

from chess import routes, models, real_time_routes
from chess.emailtoken import game_socket_token
app.jinja_env.globals.update(game_url=game_socket_token)