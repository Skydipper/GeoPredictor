# GeoPredictor
Receives a geoJson/geostore and a model and generates a prediction.

Lists all models and allows filtering by datasetID, type, architecture...

The knowledge sorce came from this [medium article](https://medium.com/@renato.groffe/postgresql-pgadmin-4-docker-compose-montando-rapidamente-um-ambiente-para-uso-55a2ab230b89)

## development
You will need to have installed docker and docker-compose; also you will  need to have control tower and geostore microservices up and running  
run `sh geopredictor.sh develop` 
 After pgadmin is up and running you can `http://0.0.0.0:16543/` to load into pg-admin
 you need to create a new server connection and in network add the docker network name, the port used on postgres and the login info (all available on the env variables)

 