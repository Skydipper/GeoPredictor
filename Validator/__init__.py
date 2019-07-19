from flask import Flask, request, jsonify
from Validator.middleware import parse_payload
import logging

app = Flask(__name__)

@app.route('/')
def hello_world(name='world'):
    """A hello world func"""
    return f"Hello {name}"

@app.route('/post',  strict_slashes=False, methods=['POST'])
@parse_payload
def post_schema(payload):
    logging.info(f'[POST]: Recieved {payload}')
    return jsonify(payload), 200