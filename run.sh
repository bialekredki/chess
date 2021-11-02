export APP_MAIL_PASSWORD="tiFBLksVU7n7tWD"
export APP_MAIL_USERNAME="chess2137linux"
celery -A chess.celery  worker --loglevel=INFO >> celery_log.txt &
flask db migrate
flask db upgrade
flask run --host=0.0.0.0
