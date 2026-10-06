from datetime import datetime

API_NAME = 'Task Manager API'
API_VERSION = '1.0'


def health():
    return {'status': 'ok', 'timestamp': str(datetime.now())}


def index():
    return {'message': API_NAME, 'version': API_VERSION}
