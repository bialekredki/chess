import requests
import json 

STATIC_DATA = 'chess/static/data/'

def get_country_from_ip(ip:str)->str:
    return requests.get(f'http://ipinfo.io/{ip}/json').json().get('country') if ip != '127.0.0.1' and not ip.startswith('192.168') else 'PL'

def country_alpha2_to_name(alpha2:str)->str:
    with open(f'{STATIC_DATA}countries_alpha2.json') as f:
        return json.load(f)[alpha2]