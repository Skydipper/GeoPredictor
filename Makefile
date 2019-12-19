.PHONY: import
import: data/gadm36_levels.gpkg
	docker-compose up
data/gadm36_levels_gpkg.zip:
	mkdir -p data/ && cd data && wget https://biogeo.ucdavis.edu/data/gadm3.6/gadm36_levels_gpkg.zip
data/gadm36_levels.gpkg: data/gadm36_levels_gpkg.zip
	cd data && unzip -u gadm36_levels_gpkg.zip
clean:
	rm -rf data/