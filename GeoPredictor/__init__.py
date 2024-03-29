import asyncio
import base64
import json
import logging
import os
import sys

import CTRegisterMicroserviceFlask
import ee
from flask import Flask, jsonify, Blueprint

from GeoPredictor.errors import error
from GeoPredictor.errors import error
from GeoPredictor.middleware import parse_payload, sanitize_parameters, get_geo_by_hash
from GeoPredictor.services import Database, predict
from GeoPredictor.validators import validate_prediction_params


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
    """Sets up logs level."""
    formatter = logging.Formatter(
        '%(asctime)s \033[1m%(levelname)s\033[0m:%(name)s:\033[1m%(funcName)s\033[0m - %(lineno)d:  %(message)s',
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

app = Flask(__name__)


# Initialization of Flask application.

# def setup_gcAccess():
#    """Sets up GCS authentication."""
#    gae_credentials = app_engine.Credentials()
#    client = storage.Client(credentials=gae_credentials)
#    config.CATALOG_BUCKET = client.get_bucket("earthengine-catalog")
# Initializing GEE

def setup_ee():
    """Sets up Earth Engine authentication."""
    try:
        private_key = base64.b64decode(os.getenv('EE_PRIVATE_KEY'))
        service_email = os.getenv('GEO_PREDICTOR_SERVICE_EMAIL')
        credentials = ee.ServiceAccountCredentials(email=service_email, key_data=private_key)
        ee.Initialize(credentials=credentials)
        ee.data.setDeadline(60000)
        app.logger.info("EE Initialized")
    except Exception as err:
        logging.error(f'{err}')
        return error(status=502, detail=f'{err}')


setup_ee()

################################################################################
# Routes handle with Blueprint is always a good idea
################################################################################
geoPredictor = Blueprint('geoPredictor', __name__)


@geoPredictor.route('/model', strict_slashes=False, methods=['GET'])
def get_models():
    # Receive a payload and post it to DB to get all models. No pagination or filtering capabilities applied yet
    try:
        db = Database()
        query = """
        SELECT model.model_name, model_type, model_output, model_description, model_versions.version as version, model_versions.model_architecture, model_versions.training_params->>'tb_url' as tb_url
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


@geoPredictor.route('/dataset', strict_slashes=False, methods=['GET'])
def get_datasets():
    # Receive a payload and post it to DB to get all models. No pagination or filtering capabilities applied yet
    try:
        db = Database()
        query = """
        SELECT  dataset.slug, dataset.name, dataset.bands, dataset.rgb_bands, dataset.provider, image.bands_selections, image.scale, image.bands_min_max
		FROM image 
		INNER JOIN dataset ON image.dataset_id=dataset.id 
        """
        result = db.Query(query)
        app.logger.debug(result)
        # function to post schema
        return jsonify(
            {'data': result}
        ), 200
    except Exception as err:
        return error(status=502, detail=f'{err}')


@geoPredictor.route('/model/<model_name>', strict_slashes=False, methods=['GET', 'POST'])
@sanitize_parameters
@validate_prediction_params
@get_geo_by_hash
def get_prediction(**kwargs):
    # app.logger.info(f"id: {model_id}")
    # function to get prediction from the selected model and region
    app.logger.info(f'[GET, POSTS]: Recieved {kwargs}')
    # Set up the loop; we need to set it up here and not in the service because is not thread safe.
    loop = asyncio.new_event_loop()
    # activate this if you need to debug async loop
    # loop.set_debug(True)
    tests = predict(loop, **kwargs)
    loop.close()
    return jsonify({
        'data': tests
    }), 200


# Routing
app.register_blueprint(geoPredictor, url_prefix='/api/v1/geopredictor')

################################################################################
# CT Registering
################################################################################
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


#
#
def load_config_json(name):
    json_path = os.path.abspath(os.path.join(PROJECT_DIR, 'microservice')) + '/' + name + '.json'
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


################################################################################
# Error handler
################################################################################

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
