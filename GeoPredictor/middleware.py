from flask import request
from functools import wraps

def parse_payload(func):
    """Get payload data"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logging.info(f'[POST]: Recieved {payload}')
        kwargs["payload"] = request.args.get('payload', {'payload': None})
        return func(*args, **kwargs)
    return wrapper