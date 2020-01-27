from GeoPredictor import app
import os

if __name__ == "__main__":
    app.run(
        host='0.0.0.0',
        debug=True,
        port='6868')
