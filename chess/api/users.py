from chess.api import *

@app.route('/api/users/top', methods=['GET'])
def api_users_top():
    response_object = dict()
    limit:int = 10 if request.args.get('limit') is None else int(request.args.get('limit'))
    names:list = EloUserRating.names()
    print(limit, request.args.get('limit'))
    for name in names:
        ratings = EloUserRating.query.order_by(text(f'{name} desc')).all()
        response_object[name] = list()
        for rating in ratings:
            user:User = rating.user
            if rating == user.get_current_rating():
                response_object[name].append((user.username, rating.by_name(name)))
            if len(response_object[name]) >= limit: break
    return (response_object, 200)
