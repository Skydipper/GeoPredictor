from flask import Flask, request, jsonify, Blueprint
import os
import sys
import CTRegisterMicroserviceFlask
import logging
#from google.auth import app_engine
import ee

from GeoPredictor.services import Database, predict
from GeoPredictor.middleware import parse_payload, sanitize_parameters, get_geo_by_hash
from GeoPredictor.validators import validate_prediction_params
from GeoPredictor.errors import error


#from bson.objectid import ObjectId
import json
import jsonschema



def setup_logLevels(level="DEBUG"):
    """Sets up Earth Engine authentication."""
    logging.basicConfig(level=level)
    formatter = logging.Formatter('%(asctime)s %(levelname)s:%(name)s:%(funcName)s - %(lineno)d:  %(message)s',
                              '%Y%m%d-%H:%M%p')

    root = logging.getLogger()
    root.setLevel(level)
    error_handler = logging.StreamHandler(sys.stderr)
    error_handler.setLevel(logging.WARN)
    error_handler.setFormatter(formatter)
    root.addHandler(error_handler)

    output_handler = logging.StreamHandler(sys.stdout)
    output_handler.setLevel(level)
    output_handler.setFormatter(formatter)
    root.addHandler(output_handler)
    logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)
    logging.getLogger('googleapiclient.discovery').setLevel(logging.ERROR)
    logging.getLogger('werkzeug').setLevel(logging.ERROR)

setup_logLevels()

# Initialization of Flask application.
app = Flask(__name__)   


# CT Registering blablabla
#PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#BASE_DIR = os.path.dirname(PROJECT_DIR)
#
#
#def load_config_json(name):
#    json_path = os.path.abspath(os.path.join(BASE_DIR, 'microservice')) + '/' + name + '.json'
#    with open(json_path) as data_file:
#        info = json.load(data_file)
#    return info
#
#info = load_config_json('register')
#swagger = load_config_json('swagger')
#CTRegisterMicroserviceFlask.register(
#    app=app,
#    name='aqueduct',
#    info=info,
#    swagger=swagger,
#    mode=CTRegisterMicroserviceFlask.AUTOREGISTER_MODE if os.getenv('CT_REGISTER_MODE') and os.getenv(
#        'CT_REGISTER_MODE') == 'auto' else CTRegisterMicroserviceFlask.NORMAL_MODE,
#    ct_url=os.getenv('CT_URL'),
#    url=os.getenv('LOCAL_URL')
#)
#@app.before_first_request
#def setup_gcAccess():
#    """Sets up Earth Engine authentication."""
#    gae_credentials = app_engine.Credentials()
#    client = storage.Client(credentials=gae_credentials)
#    config.CATALOG_BUCKET = client.get_bucket("earthengine-catalog")

def setup_ee():
    """Sets up Earth Engine authentication."""
    #private_key_file = SETTINGS.get('gee').get('privatekey_file')
    private_key = os.getenv('EE_PRIVATE_KEY')
    credentials = ee.ServiceAccountCredentials(email=None, key_data=private_key)
    ee.Initialize(credentials=credentials, use_cloud_api=False)
    ee.data.setDeadline(60000)
    app.logger.info("EE Initialized")


setup_ee()

################################################################################
# Route handlers for entry points
################################################################################

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

@app.route('/model/<model_id>',  strict_slashes=False, methods=['GET', 'POST'])
@sanitize_parameters
@validate_prediction_params
@get_geo_by_hash
def get_prediction(model_id, **kwargs):
    #app.logger.info(f"id: {model_id}")
    #function to get prediction from the selected model and region
    app.logger.info(f'[GET, POSTS]: Recieved {model_id}')
    app.logger.info(f'[GET, POSTS]: Recieved {kwargs}')
    tests = predict(**kwargs)
    #result = mongo_collection.find_one({"_id": ObjectId(schema_id)})
    #app.logger.debug(result)
    #del result["_id"]
    return jsonify({
        'data': tests
    }), 200

# Routing

@app.errorhandler(403)
def forbidden(e):
    return error(status=403, detail='Forbidden')


@app.errorhandler(404)
def page_not_found(e):
    return error(status=404, detail='Not Found')


@app.errorhandler(405)
def method_not_allowed(e):
    return error(status=405, detail='Method Not Allowed')


@app.errorhandler(410)
def gone(e):
    return error(status=410, detail='Gone')


@app.errorhandler(500)
def internal_server_error(e):
    return error(status=500, detail='Internal Server Error')
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
