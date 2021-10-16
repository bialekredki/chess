import flask_mail
from chess import mail
from flask import render_template, url_for

def send_mail(subject,recipients,url,html,sender='oskar@notchess.com'):
    if recipients is not list:
        recipients = [recipients]
    html = render_template(html, params={'url':url})
    msg = flask_mail.Message(subject, recipients=recipients, html=html, sender=sender)
    mail.send(msg)