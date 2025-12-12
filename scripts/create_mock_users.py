from app import WavvyAPIWrapper
from app.api import WavvyAPIBlueprints
from app.services.register_services import APIServices


APP = WavvyAPIWrapper(__name__).create_dev_app()
APP._services = APIServices(APP)
WavvyAPIBlueprints.register_blueprints(APP)


