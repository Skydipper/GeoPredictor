from flask import request
from functools import wraps

from GeoPredictor.errors import GeostoreNotFound
from GeoPredictor.services import GeostoreService

def parse_payload(func):
    """Get payload data"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logging.info(f'[POST]: Recieved {payload}')
        kwargs["payload"] = request.args.get('payload', {'payload': None})
        return func(*args, **kwargs)
    return wrapper

def get_geo_by_hash(func):
    """Get geostore data"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        geostore = kwargs["sanitized_params"]["geostore"]
        logging.info(f'[middleware]: {geostore}')
        try:
            geojson = GeostoreService.get(geostore)
            kwargs["sanitized_params"]["geojson"] = geojson
        except GeostoreNotFound:
            return error(status=404, detail='Geostore not found')
        
        return func(*args, **kwargs)

    return wrapper