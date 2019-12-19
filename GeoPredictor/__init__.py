from flask import Flask, request, jsonify
import CTRegisterMicroserviceFlask
import logging

from GeoPredictor.middleware import parse_payload
from GeoPredictor.validators import validate_schema_id
#from bson.objectid import ObjectId
import json
import jsonschema

app = Flask(__name__)
logging.basicConfig(level="DEBUG")

#mongo_client = MongoClient('mongodb', 27017)
#mongo_db = mongo_client.test_database
#mongo_collection = mongo_db.test_collection

@app.route('/')
def hello_world(name='world'):
    """A hello world func"""
    return f"Hello {name}"

#@app.route('/schema',  strict_slashes=False, methods=['POST'])
#def post_schema():
#    # Receive a payload and post it to mongo
#    payload = request.json
#    app.logger.debug(payload)
#    # function to post schema
#    result = mongo_collection.insert_one(payload).inserted_id
#    return jsonify(
#        {'data': str(result)}
#    ), 200
#
#@app.route('/schema/<schema_id>',  strict_slashes=False, methods=['GET'])
#def get_schema(schema_id):
#    app.logger.info(f"id: {schema_id}")
#    #function to get schema id from mongo
#    logging.info(f'[GET]: Recieved {schema_id}')
#
#    result = mongo_collection.find_one({"_id": ObjectId(schema_id)})
#    app.logger.debug(result)
#    del result["_id"]
#    return jsonify({
#        'data': result
#    })
#
#
#@app.route('/schema/<schema_id>/validate',  strict_slashes=False, methods=['POST'])
#def validate(schema_id):
#    app.logger.info(f"id: {schema_id}")
#    #function to get schema id from mongo
#    logging.info(f'[GET]: Recieved {schema_id}'),
#    schema = mongo_collection.find_one({"_id": ObjectId(schema_id)})
#
#    payload = request.json
#
#    app.logger.debug(schema)
#    app.logger.debug(payload)
#    
#    del schema["_id"]
#
#    try:
#        validation = jsonschema.validate(payload, schema)
#    except Exception as e:
#        output = str(e)
#        
#    if output is None:
#        output = "OK"
#    return jsonify({
#        'data': output
#    })
