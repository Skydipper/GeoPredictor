# GeoPredictor
Receives a geoJson/geostore id, a model and generates a prediction.

Lists all models and allows filtering by datasetID, type, architecture...  

[Working Postman collection with endpoints](https://www.getpostman.com/collections/f9a3732641b8a2dfebbc)  

The knowledge sorce came from this [medium article](https://medium.com/@renato.groffe/postgresql-pgadmin-4-docker-compose-montando-rapidamente-um-ambiente-para-uso-55a2ab230b89)  

For the AI part of the project the knowledge came from https://github.com/Skydipper/CNN-tests

## development
You will need to have installed [docker](https://docs.docker.com/install/) and [docker-compose](https://docs.docker.com/compose/install/); 

You will  need to have [control tower](https://github.com/Skydipper/control-tower/tree/skydipper) and [geostore](https://github.com/Skydipper/Geostore) up and running.

run `sh geopredictor.sh develop` 

After pgadmin is up and running you can `http://0.0.0.0:16543/` to load into pg-admin.
In order to connect with the DB you should create server connection with network as the hostname, the port, username and password that you seted up on your `.env` file

For the microservice endpoint you should be able to access `http://0.0.0.0:6868/` or if working with CT `http://0.0.0.0:9000/v1/model`
 
In order to populate the DB you will need to update the data as you need on the `/data`  folder. 
You will need to connect to the postgres container. To do so:
`docker exec -it geo-postgres-compose /bin/bash`
`cd /data_import`
`sh import_data.sh`
