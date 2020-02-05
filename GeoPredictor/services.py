import ee
import asyncio
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

def predict(loop, **kwargs):
	"""
	This function uses GEE to generate a set of tile urls to serve the model selected predicion for the user area selection.

	TODO: this will need a refactor
	"""
	try:
		# Test if the user selected model is on the database and deployed, this will then provide the Model info.
		# --- PARAMS 
		db = Database()
		geometry = kwargs['sanitized_params']['geojson']
		EE_TILES = 'https://earthengine.googleapis.com/map/{mapid}/{{z}}/{{x}}/{{y}}?token={token}'

		logging.debug('launching query...')
		query = f"""
		SELECT model.model_name, model_type, model_output, model_description, model_versions.input_image_id,model_versions.output_image_id, model_versions.kernel_size, model_versions.version as version, model_versions.model_architecture, model_versions.training_params 
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

		# Get the image input and output information
		# TODO: right now we are not really separating which is the input and witch is the output, we should 
		
		query_2 = f"""
		SELECT  dataset.slug, dataset.name, dataset.bands, dataset.rgb_bands, dataset.provider, image.bands_selections, image.scale, image.bands_min_max
		FROM image 
		INNER JOIN dataset ON image.dataset_id=dataset.id
		WHERE image.id in ({modelData[0]["input_image_id"]}, {modelData[0]["output_image_id"]})
			"""
		iImageData, oImageData = db.Query(query_2)
		
		logging.debug(f'[INPUT]: {iImageData}')
		logging.debug(f'[OUTPUT]: {oImageData}')
		
		
		
		# Create composite
		# TODO: 
		# * right now the composite specifics are on a separate file, `ee_collection_specifics` this is does not scale at all, we should add this information to the DB  to image and dataset info
		# * asyncronously fetch mapids, as generating the info might take some time

		image = ee_collection_specifics.Composite(iImageData['slug'])(kwargs['sanitized_params']['init_date'], kwargs['sanitized_params']['end_date'])
		
		# Normalize Input image composite
		if bool(iImageData['bands_min_max']): 
			image = normalize_ee_images(image, iImageData["slug"], json.loads(iImageData["bands_min_max"]))
		image = image.select(json.loads(modelData[0]["training_params"])["in_bands"]).float()

		logging.debug(f'[image]: {image.getInfo()}')
		
		# Predicted image composite
		
		# Load the trained model and use it for prediction.
		model_name = str(modelData[0]["model_name"])
		logging.debug(f"[MODEL NAME]: {model_name}")
		version_name = 'v'+ str(modelData[0]["version"])
		logging.debug(f"[INPUT- VERSION]: {version_name}")
		kernel_size = int(modelData[0]["kernel_size"])
		logging.debug(f"[KERNEL SIZE]: {kernel_size}")

		if kernel_size == 1:
		    input_tile_size = [1, 1]
		    input_overlap_size = [0, 0]
		if kernel_size >1 :
		    input_tile_size = [144, 144]
		    input_overlap_size = [8, 8]

		model = ee.Model.fromAiPlatformPredictor(
			projectName = os.getenv('project_id'),
			modelName = model_name,
			version = version_name,
			inputTileSize = input_tile_size,
			inputOverlapSize = input_overlap_size,
			proj = ee.Projection('EPSG:4326').atScale(iImageData["scale"]),
			fixInputProj = True,
			outputBands = {'prediction': {
				'type': ee.PixelType.float(),
				'dimensions': 1,
			}                  
			}
		)
		predictions = model.predictImage(image.toArray()).arrayFlatten([json.loads(modelData[0]["training_params"])["out_bands"]])

		logging.debug(f'[predictions]: {predictions.getInfo()}')
		# Get the Geometry information
		
		#logging.debug(f"[MY GEOM]{geometry}")
		polygon = ee.Geometry.Polygon(json.loads(geometry).get('features')[0].get('geometry').get('coordinates'))
		
		# Clip the prediction area with the polygon
		predictions = predictions.clip(polygon)

		if modelData[0]["model_output"] == 'segmentation':
			maxValues = predictions.reduce(ee.Reducer.max())

			predictions = predictions.addBands(maxValues)

			expression = ""
			for n, band in enumerate(json.loads(modelData[0]["training_params"])["out_bands"]):
				expression = expression + f"(b('{band}') == b('max')) ? {str(n+1)} : "

			expression = expression + f"0"

			segmentation = predictions.expression(expression)
			predictions = predictions.addBands(segmentation.mask(segmentation).select(['constant'], ['categories']))

		# Prepare the output
		# TODO: We will need to set up a REDIS to cache mapids and and GCS to store images and tiles for prediction so we don't get lost and a redirection/proxy functionality.
		logging.debug(f"[ASYNC] Init")
		

		#logging.debug(f"[INPUT- rgbBands]: {iImageData['rgb_bands']}")
		
		iMapids = []
		iParams =[{'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 1}]
		iMapids.append(image.getMapId(iParams[0]))
		
		oMapids = []
		if  modelData[0]["model_type"] == 'segmentation':
			oParams =[{'bands': ['categories'], 'min': 1, 'max': len(json.loads(modelData[0]["training_params"])["out_bands"])}]
		else:
			oParams =[{'bands': [band], 'min': 0, 'max': 1} for band in json.loads(modelData[0]["training_params"])["out_bands"]]
		
		
		asyncio.set_event_loop(loop)
		logging.debug(f"[ASYNC] Initiating loop.")
		tasks = [get_MapId(predictions, m) for m in oParams]
		# Fulfill promises
		logging.debug(f"'[ASYNC] looping through functios .'")
		oMapids = loop.run_until_complete(asyncio.gather(*tasks))
		
		result = {
			'centroid': polygon.centroid().getInfo().get('coordinates')[::-1],
			'inputImage': [EE_TILES.format(**iMapid) for iMapid in iMapids],
			'outputImage': [EE_TILES.format(**oMapid) for oMapid in oMapids],
		}
		return result
	except Exception as err:
		raise Error(err)
	finally:
		loop.close()
		

async def get_MapId(image, params):
			logging.debug(f"[ASYNC loop]: {params}")
			return image.getMapId(params)

