import ee
import logging
import os
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

def predict(**kwargs):
	try:
		db = Database()
		logging.debug('launching query...')
		query = f"""
			SELECT model.model_name, model_type, model_description, model_versions.version as version, model_versions.model_architecture 
        FROM model 
        INNER JOIN model_versions ON model.id=model_versions.model_id
        WHERE deployed is true 
			AND model_name='{kwargs['sanitized_params']['model_name']}'"""
		if kwargs['sanitized_params']['model_version']=='last':
			query = query + ' ORDER BY version DESC LIMIT 1'
		else:
			query = query + f" AND version = {kwargs['sanitized_params']['model_version']}"
		result = db.Query(query)
		if not result:
			logging.error(result)
			raise ModelError('model not found')
		logging.debug(f"DB: {result}")
		return result
	except Exception as err:
		raise Error(err)
