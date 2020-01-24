"""ERRORS"""
from flask import jsonify


def error (status=500, detail = 'generic error'):
    error = {
        'status': status,
        'detail': detail
    }
    return jsonify(errors=[error]), status

class Error(Exception):

    def __init__(self, message):
        self.message = message

    @property
    def serialize(self):
        return {
            'message': self.message
        }


class CartoError(Error):
    pass


class GeostoreNotFound(Error):
    pass


class DBError(Error):
    pass


class GeocodeError(Error):
    pass