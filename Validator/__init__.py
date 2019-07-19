from flask import Flask, request, jsonify
from Validator.middleware import parse_payload
import logging
from Validator.validators import validate_schema_id

app = Flask(__name__)
logging.basicConfig(level="DEBUG")



@app.route('/')
def hello_world(name='world'):
    """A hello world func"""
    return f"Hello {name}"

@app.route('/schema',  strict_slashes=False, methods=['POST'])
@parse_payload
def post_schema(payload):
    logging.info(f'[POST]: Recieved {payload}')
    # function to post schema

    return jsonify(payload), 200

@app.route('/schema/<id>',  strict_slashes=False, methods=['GET'])
@validate_schema_id
def get_schema(id):
    #function to get schema id from mongo
    logging.info(f'[GET]: Recieved {id}')
    return f"{id}"