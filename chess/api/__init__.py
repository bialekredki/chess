from datetime import datetime
from re import S
import re
from typing import Union
from flask.helpers import flash
from flask.json import jsonify
from flask.wrappers import Response
from flask_login.utils import login_required
from sqlalchemy.sql.elements import conv
from sqlalchemy.sql import text
from chess import app, db, socketio, mail, celery, auth
from flask import render_template, redirect, url_for, request
from chess.AI import AI_INTEGRATIONS_NAMES_LIST, StockfishIntegrationAI, StupidAI, get_ai, PREFERRED_INTEGRATION
from chess.forms import ForgotPasswordForm, LoginForm, RegisterForm, SettingsForm
from chess.game import Move, MovesOrdering, PieceType
from chess.game_options import GameFormat, GameOption
from chess.game import Game as ChessGame
from chess.geolocation import get_country_from_ip
from chess.models import BlogPost, BlogPostComment, ChessBoardTheme, GameState, MatchmakerRequest, Message, RecoveryTry, User, Game, EloUserRating
import flask_mail
from flask_login import current_user, login_user, logout_user
from chess.emailtoken import confirm_email_token, confrim_recovery_token, friendship_request_token, generate_email_token, generate_matchmaking_token, generate_recovery_token, generate_game_invitation_token, confirm_game_invitation_token, get_friendship_request_token, get_game_socket_token, resolve_matchmaking_token, game_socket_token
from chess.utils import round_datetime
from sqlalchemy import or_
from flask_socketio import SocketIO,send,emit
from PIL import Image
import json
from fuzzywuzzy import fuzz
import os.path
from chess.mail import send_mail
from chess.background import check_expired_games, on_raw_message, matchmaker_task

from flask import g
from .account import *
from .authentication import *
from .users import *
from .bots import *
from .utils import verify_request

