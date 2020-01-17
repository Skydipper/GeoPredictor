# GeoPredictor
Receives a geoJson/geostore and a model and generates a prediction.

Lists all models and allows filtering by datasetID, type, architecture...

The knowledge sorce came from this [medium article](https://medium.com/@renato.groffe/postgresql-pgadmin-4-docker-compose-montando-rapidamente-um-ambiente-para-uso-55a2ab230b89)

## development
You will need to have installed docker and docker-compose; 
You will  need to have control tower and geostore microservices up and running.

run `sh geopredictor.sh develop` 
 After pgadmin is up and running you can `http://0.0.0.0:16543/` to load into pg-admin.
 for the microservice endpoint you should be able to access `http://0.0.0.0:6868/`
 
In order to populate the DB you will need to update the data as you need on the `/data`  folder. 
You will need to connect to the postgres container. To do so:
`docker exec -it geo-postgres-compose /bin/bash
`
`cd /data_import`
`sh import_data.sh`
