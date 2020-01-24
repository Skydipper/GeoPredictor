from flask import request
from functools import wraps
import logging
from cerberus import Validator
from GeoPredictor.errors import error


def myCoerc(n):
    try:
        return lambda v: None if v in ('null') else n(v)
    except Exception:
        return None


null2int = myCoerc(int)
null2float = myCoerc(float)

to_bool = lambda v: v.lower() in ('true', '1')
to_lower = lambda v: v.lower()
# to_list = lambda v: json.loads(v.lower())
to_list = lambda v: json.loads(v)

def validate_prediction_params(func):
    """Water Risk atlas parameters validation"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        validation_schema = {
            'geostore': {
                'type': 'string',
                'excludes': 'geojson',
                'required': True
            },
            'geojson': {
                'type': 'string',
                'excludes': 'geostore',
                'required': True
            },
            'model_name': {
                'type': 'string',
                'required': True,
                'default': None
            },
            'model_version': {
                'type': 'string',
                'required': False,
                'default': 'last',
                'coerce': to_lower
            }
            
        }
        rArgs = {**request.args, **request.json}
        kwargs.update(rArgs)  
        logging.debug(f"[VALIDATOR - prediction params]: {kwargs}")
        validator = Validator(validation_schema, purge_unknown=True)

        if not validator.validate(kwargs):
            return error(status=400, detail=validator.errors)
        kwargs['sanitized_params'] = validator.normalized(kwargs)
        return func(*args, **kwargs)

    return wrapper