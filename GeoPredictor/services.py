import ee
from GeoPredictor import ee_collection_specifics
import logging
import os
import json
from sqlalchemy import create_engine
from CTRegisterMicroserviceFlask import request_to_microservice

from GeoPredictor.errors import GeostoreNotFound, error, ModelError, Error
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

		except Exception as err:
			return error(status=502, detail=f'{err}')
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
		logging.debug(f"{query}")
		fetchQuery = self.connection.execute(f"{query}")
		output = [{column: value for column, value in rowproxy.items()} for rowproxy in fetchQuery]
			
		return output

#normalize
def normalize_ee_images(image, collection, values):
	
	Bands = ee_collection_specifics.ee_bands(collection)
	   
	# Normalize [0, 1] ee images
	for i, band in enumerate(Bands):
		if i == 0:
			image_new = image.select(band).clamp(values[band+'_min'], values[band+'_max'])\
								.subtract(values[band+'_min'])\
								.divide(values[band+'_max']-values[band+'_min'])
		else:
			image_new = image_new.addBands(image.select(band).clamp(values[band+'_min'], values[band+'_max'])\
									.subtract(values[band+'_min'])\
									.divide(values[band+'_max']-values[band+'_min']))
			
	return image_new

def predict(**kwargs):
	try:
		# Test if the user selected model is on the database and deployed, this will then provide the Model info.
		db = Database()
		logging.debug('launching query...')
		query = f"""
		SELECT model.model_name, model_type, model_description,model_versions.input_image_id,model_versions.output_image_id, model_versions.version as version, model_versions.model_architecture, model_versions.training_params 
		FROM model 
		INNER JOIN model_versions ON model.id=model_versions.model_id
		WHERE deployed is true 
			AND model_name='{kwargs['sanitized_params']['model_name']}'
			"""
		if kwargs['sanitized_params']['model_version']=='last':
			query = query + ' ORDER BY version DESC LIMIT 1'
		else:
			query = query + f" AND version = {kwargs['sanitized_params']['model_version']}"
		
		modelData = db.Query(query)
		if not modelData:
			logging.error(modelData)
			raise ModelError('model not found')
		if len(modelData) > 1:
			logging.error(modelData)
			raise ModelError('too many models')

		logging.debug(f"DB: {modelData}")

		# Get the image input and output information
		
		query_2 = f"""
		SELECT  dataset.slug, dataset.name, dataset.bands, dataset.rgb_bands, dataset.provider, image.band_selections, image.scale, image.bands_min_max
		FROM image 
		INNER JOIN dataset ON image.dataset_id=dataset.id
		WHERE image.id in ({modelData[0]["input_image_id"]}, {modelData[0]["output_image_id"]})
			"""
		iImageData, oImageData = db.Query(query_2)
		logging.debug(f'[INPUT]: {iImageData}')
		logging.debug(f'[OUTPUT]: {oImageData}')
		
		
		
		# Create composite
		image = ee_collection_specifics.Composite(iImageData['slug'])(kwargs['sanitized_params']['init_date'], kwargs['sanitized_params']['end_date'])
		
		# Normalize Input image composite
		if bool(iImageData['bands_min_max']): 
			image = normalize_ee_images(image, iImageData['slug'], iImageData['bands_min_max'])
		image = image.select(modelData[0]["training_params"]["in_bands"]).float()
		
		
		# Predicted image composite
		
		# Load the trained model and use it for prediction.
		version_name = 'v'+ str(modelData[0]["version"])
		logging.debug(f"[INPUT- VERSION]: {version_name}")
		model = ee.Model.fromAiPlatformPredictor(
			projectName = os.getenv('project_id'),
			modelName = modelData[0]["model_name"],
			version = version_name,
			inputTileSize = [144, 144],
			inputOverlapSize = [8, 8],
			proj = ee.Projection('EPSG:4326').atScale(iImageData["scale"]),
			fixInputProj = True,
			outputBands = {'prediction': {
				'type': ee.PixelType.float(),
				'dimensions': 1,
			}                  
			}
		)
		predictions = model.predictImage(image.toArray()).arrayFlatten([modelData[0]["training_params"]["out_bands"]])

		# Get the Geometry information
		geometry = kwargs['sanitized_params']['geojson']
		logging.debug(f"[MY GEOM]{geometry}")
		polygon = ee.Geometry.Polygon(json.loads(geometry).get('features')[0].get('geometry').get('coordinates'))
		
		# Clip the prediction area with the polygon
		predictions = predictions.clip(polygon)

		if modelData[0]["model_type"] == 'segmentation':
			maxValues = predictions.reduce(ee.Reducer.max())

			predictions = predictions.addBands(maxValues)

			expression = ""
			for n, band in enumerate(modelData[0]["training_params"]["out_bands"]):
				expression = expression + f"(b('{band}') == b('max')) ? {str(n+1)} : "

			expression = expression + f"0"

			segmentation = predictions.expression(expression)
			predictions = predictions.addBands(segmentation.mask(segmentation).select(['constant'], ['categories']))

		EE_TILES = 'https://earthengine.googleapis.com/map/{mapid}/{{z}}/{{x}}/{{y}}?token={token}'

		logging.debug(f"[INPUT- rgbBands]: {iImageData['rgb_bands']}")
		iMapid = image.getMapId({'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 1})

		if  modelData[0]["model_type"] == 'segmentation':
			oMapid = predictions.getMapId({'bands': ['categories'], 'min': 1, 'max': len(modelData[0]["training_params"]["out_bands"])})
		else:
			oMapid = {}
			#for band in modelData[0]["training_params"]["out_bands"]:
			#	mapid = predictions.getMapId({'bands': [band], 'min': 0, 'max': 1})


		result = {
			'centroid': polygon.centroid().getInfo().get('coordinates')[::-1],
			'inputImage': EE_TILES.format(**iMapid),
			'outputImage': EE_TILES.format(**oMapid),
		}
		return result
	except Exception as err:
		raise Error(err)




