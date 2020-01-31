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
	model_description TEXT,
	output_image_id INT
		
);
CREATE TABLE model_versions (
	id INT PRIMARY KEY,
	model_id INT,
	model_architecture TEXT,
	input_image_id INT,
	output_image_id INT,
	geostore_id TEXT,
	sample_size INT,
	training_params JSONB,
	version BIGINT,
	data_status TEXT,
	training_status TEXT,
	eeified BOOL,
	deployed BOOL
);
CREATE TABLE image (  
	id INT PRIMARY KEY,
	dataset_id INT,
	band_selections TEXT,
	scale FLOAT,
	init_date DATE,
	end_date DATE,
	bands_min_max JSONB
);
CREATE TABLE dataset (
	id INT PRIMARY KEY,
	slug TEXT,
	name TEXT,
	bands TEXT,
	rgb_bands TEXT,
	provider TEXT
	
	
	
	
);
OMG
echo "NOTICE:  finish creating tables."
for NAME in ${TABLES}; do
	echo "TABLE: \033[94m ${NAME}\033[0m"
	psql -U ${THE_USER} ${THE_DB} <<OMG
    DELETE FROM ${NAME}; 
    COPY ${NAME} FROM '${THE_DIR}${NAME}.csv' quote '^' delimiter ';' CSV header;
OMG
done

# alter datatypes for tables image and dataset to convert band data from text onto an array
echo "\033[92mSUCCESS:\033[0m  Formatting arrays..."
psql -U ${THE_USER} ${THE_DB}<<OMG
ALTER TABLE image
ALTER COLUMN band_selections TYPE jsonb USING to_jsonb(band_selections);

ALTER TABLE dataset
ALTER COLUMN bands TYPE jsonb USING to_jsonb(bands);

ALTER TABLE dataset
ALTER COLUMN rgb_bands TYPE jsonb USING to_jsonb(rgb_bands);
OMG

echo "\033[92mSUCCESS:\033[0m  Tables import ready"