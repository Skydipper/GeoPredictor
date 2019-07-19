from flask import request, jsonify
from functools import wraps
import logging

def error (status=500, detail = 'generic error'):
    error = {
        'status': status,
        'detail': detail
    }
    return jsonify(errors=[error]), status

def validate_schema_id(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        logging.info(f'[VALIDATOR]: args = {args}, kwargs = {kwargs}')
        
        schema_id = kwargs.get('id', None)

        if not schema_id :
            return error(status= 400, detail=f"Schema id: {schema_id} not found")
        if not all([c.isalnum() or c== '-' for c in schema_id]):
            return error(status= 400, detail=f"Bad schema id: {schema_id}")
        return schema_id
    
    return wrapper