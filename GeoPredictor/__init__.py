from flask import Flask, request, jsonify
import CTRegisterMicroserviceFlask
import logging
import ee

from GeoPredictor.services import .
from GeoPredictor.middleware import parse_payload
from GeoPredictor.validators import validate_schema_id

from sqlalchemy import create_engine
#from bson.objectid import ObjectId
import json
import jsonschema


gee = SETTINGS.get('gee')
gee_credentials = ServiceAccountCredentials.from_p12_keyfile(
    gee.get('service_account'),
    gee.get('privatekey_file'),
    scopes=ee.oauth.SCOPE
)
ee.Initialize(gee_credentials)
ee.data.setDeadline(60000)


app = Flask(__name__)
logging.basicConfig(level="DEBUG")

class Database():
    # replace the user, password, hostname and database according to your configuration according to your information
    engine = create_engine('postgresql://postgres:postgres@geo-postgres-compose:5432/geomodels')
    def __init__(self):
        self.connection = self.engine.connect()
        print("DB Instance created")
    
    def Query(self, query):
        fetchQuery = self.connection.execute(f"{query}")
        output = [{column: value for column, value in rowproxy.items()} for rowproxy in fetchQuery]
            
        return output

@app.route('/model',  strict_slashes=False, methods=['GET'])
def get_models():
    # Receive a payload and post it to mongo
    ##payload = request.json
    db = Database()
    result = db.Query('select * from public.model')
    app.logger.debug(result)
    # function to post schema
    return jsonify(
        {'data': result}
    ), 200
#
#@app.route('/model/<model_id>',  strict_slashes=False, methods=['GET', 'POST'])
#def get_prediction(model_id):
#    app.logger.info(f"id: {model_id}")
#    #function to get prediction from the selected model and region
#    logging.info(f'[GET, POSTS]: Recieved {model_id}')
#
#    result = mongo_collection.find_one({"_id": ObjectId(schema_id)})
#    app.logger.debug(result)
#    del result["_id"]
#    return jsonify({
#        'data': result
#    })
#
#
#@app.route('/model/<model_id>/<band>/<z>/<x>/<y>',  strict_slashes=False, methods=['GET'])
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
