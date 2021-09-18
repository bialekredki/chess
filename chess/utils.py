from datetime import datetime, timedelta


def round_datetime(td:timedelta) -> str:
    if td.days != 0: return f'{td.days} day{is_plural(td.days)} ago'
    elif td.seconds >= 60:
        d,r = divmod(td.seconds,60)
        if d < 60: return f'{d} minute{is_plural(d)} ago'
        d,r = divmod(td.seconds,60*60)
        if d < 24: return f'{d} hour{is_plural(d)} ago'
        print('xd')
    else: return 'now'

def is_plural(value:int)->str:
    if value > 1: return 's'
    return ''

    