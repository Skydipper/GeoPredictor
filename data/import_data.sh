#!/bin/sh

THE_USER=postgres
THE_DB=geomodels
PSQL=/opt/postgresql/bin/psql
THE_DIR=/data_import/
TABLES="model model_versions image dataset"


if psql -U ${THE_USER} -lqt | cut -d \| -f 1 | grep -qw ${THE_DB} 
then
    # database exists
    echo 'NOTICE:  Database '${THE_DB}' exists; Generating tables...'
else
    echo 'NOTICE:  Database does not exist; creating ${THE_DB} ...'
    ## this will help us create the database
	psql -U ${THE_USER}<<OMG
	CREATE DATABASE ${THE_DB};
OMG

fi

## this will help us create the database model
psql -U ${THE_USER} ${THE_DB}<<OMG
DROP TABLE IF EXISTS model, model_versions, image, dataset;
OMG
echo "NOTICE:  finish deleting tables."
psql -U ${THE_USER} ${THE_DB}<<OMG
CREATE TABLE model (
	id INT PRIMARY KEY,
	model_name TEXT,
	model_type TEXT,
	model_architecture TEXT,
	model_description TEXT,
	input_dataset_id TEXT,
	output_dataset_id TEXT,
	status TEXT,
	eeified BOOL,
	deployed BOOL,
	n_versions INT
	
);
CREATE TABLE model_versions (
	id INT PRIMARY KEY,
	model_id TEXT,
	geostore_id TEXT,
	sample_size INT,
	training_params JSONB,
	version INT,
	status TEXT,
	input_image_id INT,
	output_image_id INT
);
CREATE TABLE image (  
	id INT PRIMARY KEY,
	dataset_id INT,
	band_selections TEXT[],
	scale INT,
	init_date DATE,
	end_date DATE,
	composite_method TEXT,
	status INT,
	bands_min_max JSONB,
	name TEXT
);
CREATE TABLE dataset (
	id INT PRIMARY KEY,
	slug TEXT,
	name TEXT,
	bands TEXT[],
	rgb_bands TEXT[],
	provider TEXT
	
	
	
	
);
OMG
echo "NOTICE:  finish creating tables."
for NAME in ${TABLES}; do
	echo "TABLE:  ${NAME}"
	psql -U ${THE_USER} ${THE_DB} <<OMG
    DELETE FROM ${NAME}; 
    COPY ${NAME} FROM '${THE_DIR}${NAME}.csv' quote '^' delimiter ';' CSV header;
OMG
done

echo "SUCCESS:  Tables import ready"