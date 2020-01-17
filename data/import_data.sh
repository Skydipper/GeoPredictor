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
	uid TEXT,
	model_name TEXT,
	model_description TEXT,
	model_type TEXT,
	input_image_id TEXT,
	output_image_id TEXT,
	n_versions INT,
	model_architecture TEXT
);
CREATE TABLE model_versions (
	id INT PRIMARY KEY,
	model_id TEXT,
	geostore_id TEXT,
	version INT,
	training_params JSONB,
	status INT
);
CREATE TABLE image (  
	id INT PRIMARY KEY,
	uid TEXT,
	name TEXT,
	dataset_id TEXT,
	band_selection INT[],
	scale INT,
	init_date DATE,
	end_date DATE,
	composite_method TEXT,
	status INT,
	bands_min_max JSONB
);
CREATE TABLE dataset (
	id INT PRIMARY KEY,
	uid TEXT,
	dataset_id INT,
	name TEXT,
	bands JSONB,
	rgb_bands JSONB,
	provider INT
);
OMG
echo "NOTICE:  finish creating tables."
for NAME in ${TABLES}; do
	psql -U ${THE_USER} ${THE_DB} <<OMG
    DELETE FROM ${NAME}; 
    COPY ${NAME} FROM '${THE_DIR}${NAME}.csv' delimiter ',' CSV header;
OMG
done

echo "SUCCESS:  Tables import ready"