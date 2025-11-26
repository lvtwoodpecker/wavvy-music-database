# Entry point for any of the FastAPI services
# The main.py file can be used to run the FastAPI application

from . import WavvyAPIWrapper
from app.services.register_services import APIServices
from app.api import WavvyAPIBlueprints

APP = WavvyAPIWrapper(__name__).create_dev_app()
APP._services = APIServices(APP)
WavvyAPIBlueprints.register_blueprints(APP)

if __name__ == "__main__":
    APP.run(port=5000, debug=True)