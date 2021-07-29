import logging
from functools import wraps

from flask import request

from GeoPredictor.errors import GeostoreNotFound, error
from GeoPredictor.services import GeostoreService


def remove_keys(keys, dictionary):
    for key in keys:
        try:
            del dictionary[key]
        except KeyError:
            pass
        except Exception as err:
            return error(status=502, detail=f'{err}')
    return dictionary


def sanitize_parameters(func):
    """Sets any queryparams in the kwargs"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            logging.debug(f'[middleware] [sanitizer] args: {args}')
            logging.debug(f'[middleware] [sanitizer] kargs: {kwargs}')

            myargs = {**kwargs, **request.args, **request.args.get('payload', {})}
            logging.debug(f'[middleware] [sanitizer] User_args: {myargs}')
            # Exclude params like loggedUser here

            sanitized_args = remove_keys(['loggedUser'], myargs)
            kwargs['params'] = sanitized_args
        except GeostoreNotFound:
            return error(status=404, detail='body params not found')
        except Exception as err:
            return error(status=502, detail=f'{err}')

        return func(*args, **kwargs)

    return wrapper


def parse_payload(func):
    """Get payload data"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        kwargs["payload"] = request.args.get('payload', {'payload': None})
        return func(*args, **kwargs)

    return wrapper


def get_geo_by_hash(func):
    """Get geostore data"""

    @wraps(func)
    def wrapper(*args, **kwargs):

        try:
            if 'geostore' in kwargs["sanitized_params"].keys():
                geostore = kwargs["sanitized_params"]["geostore"]
                logging.info(f'[middleware]: {geostore}')
                geojson = GeostoreService.get(geostore)
                kwargs["sanitized_params"]["geojson"] = geojson
        except GeostoreNotFound:
            return error(status=404, detail='Geostore not found')
        except Exception as err:
            return error(status=502, detail=f'{err}')

        return func(*args, **kwargs)

    return wrapper
