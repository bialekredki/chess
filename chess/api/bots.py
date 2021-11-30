from chess.api import *

@app.route('/api/bots', methods=['GET'])
def api_bots():
    return ({'preferred': PREFERRED_INTEGRATION, 'integrations': AI_INTEGRATIONS_NAMES_LIST}, 200)