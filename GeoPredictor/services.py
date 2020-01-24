import ee
import logging
import os
from sqlalchemy import create_engine
#from CTRegisterMicroserviceFlask import request_to_microservice

from GeoPredictor.errors import GeostoreNotFound
#geostore connexion class
class GeostoreService(object):
    """."""

    @staticmethod
    def execute(config):
        try:
            response = request_to_microservice(config)
            if not response or response.get('errors'):
                raise GeostoreNotFound
            geostore = response.get('data', None).get('attributes', None)
            geojson = geostore.get('geojson', None).get('features', None)[0]

        except Exception as e:
            raise GeostoreNotFound(message=str(e))
        return geojson

    @staticmethod
    def get(geostore):
        config = {
            'uri': '/geostore/' + geostore,
            'method': 'GET'
        }
        return GeostoreService.execute(config)

#database connexion class
class Database():
    DBURL=os.getenv('POSTGRES_CONNECTION')
    logging.info(f"DB URL: {DBURL}")
    engine = create_engine(DBURL)
    def __init__(self):
        self.connection = self.engine.connect()
        logging.info("DB Instance created")
    
    def Query(self, query):
        fetchQuery = self.connection.execute(f"{query}")
        output = [{column: value for column, value in rowproxy.items()} for rowproxy in fetchQuery]
            
        return output

def predict(**kwargs):
	model_name = 'segmentation_0_1'
	db = Database()
	result = db.Query(f"select * from model where model_name='{model_name}'")
	
	logging.info(f"DB: {result}")
	return result
	#datasets = pd.read_csv('Database/dataset.csv', index_col=0)
	#images = pd.read_csv('Database/image.csv', index_col=0)
	#models = pd.read_csv('Database/model.csv', index_col=0)
	#versions = pd.read_csv('Database/model_versions.csv', index_col=0, dtype = {'model_id': pd.Int64Dtype(), 'version': pd.Int64Dtype()})
	#model_name = 'segmentation_0_1'
	#model_id = models[models['model_name'] == model_name].index[0]
	#model_type = models.iloc[model_id]['model_type']
	#version_names = list(map(lambda x: int(x), list(versions[versions['model_id'] == model_id]['version'])))
	#version = version_names[0]
	#version_id = versions[versions['version'] == version].index[0]
	#version_name = 'v'+ str(version)
	#version_id = versions[versions['version'] == version].index[0]
	#training_params =json.loads(versions[versions['version'] == version]['training_params'][version_id])
	#image_ids = list(versions.iloc[version_id][['input_image_id', 'output_image_id']])
	#collections = list(datasets.iloc[list(images.iloc[image_ids]['dataset_id'])]['slug'])
	#bands = [training_params.get('in_bands'), training_params.get('out_bands')]
	#scale, init_date, end_date = list(images.iloc[image_ids[0]][['scale', 'init_date', 'end_date']])
	#scale = float(scale)
	#project_id = env.project_id

	#model = ee.Model.fromAiPlatformPredictor(
	#    projectName = project_id,
	#    modelName = model_name,
	#    version = version_name,
	#    inputTileSize = [144, 144],
	#    inputOverlapSize = [8, 8],
	#    proj = ee.Projection('EPSG:4326').atScale(scale),
	#    fixInputProj = True,
	#    outputBands = {'prediction': {
	#        'type': ee.PixelType.float(),
	#        'dimensions': 1,
	#      }                  
	#    }
	#)
	#predictions = model.predictImage(image.toArray()).arrayFlatten([bands[1]])
	#predictions.getInfo()
	## Clip the prediction area with the polygon
	#polygon = ee.Geometry.Polygon(geometry.attributes.get('geojson').get('features')[0].get('geometry').get('coordinates'))
	#predictions = predictions.clip(polygon)

	## Get centroid
	#centroid = polygon.centroid().getInfo().get('coordinates')[::-1]
	#if model_type == 'segmentation':
	#    maxValues = predictions.reduce(ee.Reducer.max())

	#    predictions = predictions.addBands(maxValues)

	#    expression = ""
	#    for n, band in enumerate(bands[1]):
	#        expression = expression + f"(b('{band}') == b('max')) ? {str(n+1)} : "

	#    expression = expression + f"0"

	#    segmentation = predictions.expression(expression)
	#    predictions = predictions.addBands(segmentation.mask(segmentation).select(['constant'], ['categories']))

	#EE_TILES = 'https://earthengine.googleapis.com/map/{mapid}/{{z}}/{{x}}/{{y}}?token={token}'

	#mapid = image.getMapId({'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 1})
	#if model_type == 'segmentation':
	#    mapid = predictions.getMapId(vis_params={'bands': ['categories'], 'min': 1, 'max': len(bands[1])})