from flask import Flask, request, jsonify, Blueprint
import os
import sys
import asyncio
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

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

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

#def setup_gcAccess():
#    """Sets up GCS authentication."""
#    gae_credentials = app_engine.Credentials()
#    client = storage.Client(credentials=gae_credentials)
#    config.CATALOG_BUCKET = client.get_bucket("earthengine-catalog")

def setup_ee():
    """Sets up Earth Engine authentication."""
    try:
        private_key = os.getenv('EE_PRIVATE_KEY')
        credentials = ee.ServiceAccountCredentials(email=None, key_data=private_key)
        ee.Initialize(credentials=credentials, use_cloud_api=False)
        ee.data.setDeadline(60000)
        app.logger.info("EE Initialized")
    except Exception as err:
            return error(status=502, detail=f'{err}')


setup_ee()

################################################################################
# Routes handle with Blueprint is allways a good idea
################################################################################
geoPredictor = Blueprint('geoPredictor', __name__)

@geoPredictor.route('/model',  strict_slashes=False, methods=['GET'])
def get_models():
    # Receive a payload and post it to mongo
    try:
        db = Database()
        query = """
        SELECT model.model_name, model_type, model_description, model_versions.version as version, model_versions.model_architecture 
        FROM model 
        INNER JOIN model_versions ON model.id=model_versions.model_id
        WHERE deployed is true
        ORDER BY model_name ASC, version ASC 
        """
        result = db.Query(query)
        app.logger.debug(result)
        # function to post schema
        return jsonify(
            {'data': result}
        ), 200
    except Exception as err:
            return error(status=502, detail=f'{err}')

@geoPredictor.route('/model/<model_name>',  strict_slashes=False, methods=['GET', 'POST'])
@sanitize_parameters
@validate_prediction_params
@get_geo_by_hash
def get_prediction(**kwargs):
    #app.logger.info(f"id: {model_id}")
    #function to get prediction from the selected model and region
    app.logger.info(f'[GET, POSTS]: Recieved {kwargs}')
    #Set up the loop; we need to set it up here and not in the service because is not thread safe.
    loop = asyncio.new_event_loop()
    # activate this if you need to debug async loop
    #loop.set_debug(True)
    tests = predict(loop, **kwargs)
    loop.close()
    return jsonify({
        'data': tests
    }), 200

# Routing Errors & CT
# Routing
app.register_blueprint(geoPredictor, url_prefix='/api/v1/geopredictor')

# CT Registering
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(PROJECT_DIR)
#
#
def load_config_json(name):
    json_path = os.path.abspath(os.path.join(BASE_DIR, 'api/microservice')) + '/' + name + '.json'
    with open(json_path) as data_file:
        info = json.load(data_file)
    return info
#
info = load_config_json('register')
swagger = load_config_json('swagger')
CTRegisterMicroserviceFlask.register(
    app=app,
    name='geoPredictor',
    info=info,
    swagger=swagger,
    mode=CTRegisterMicroserviceFlask.AUTOREGISTER_MODE if os.getenv('CT_REGISTER_MODE') and os.getenv(
        'CT_REGISTER_MODE') == 'auto' else CTRegisterMicroserviceFlask.NORMAL_MODE,
    ct_url=os.getenv('CT_URL'),
    url=os.getenv('LOCAL_URL')
)

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

