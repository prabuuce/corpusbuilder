USER_AGENT = "corpusbuilder2; My User Agent Here"
COUCHDB_SERVER = 'http://localhost:5984/'
COUCHDB_DATABASE = 'corpusbuilder2'
DEBUG = True
TESTING = False
SECRET_KEY = 'not_a_secret'
HOST='127.0.0.1'
PORT="5000"

BROKER_BACKEND = "couchdb"
BROKER_HOST = "localhost"
BROKER_PORT = 5984
BROKER_VHOST = "celery"

CELERY_BROKER_URL='redis://localhost:6379/0'
CELERY_RESULT_BACKEND='redis://localhost:6379/0'
CELERYD_CONCURRENCY = 2
CELERY_QUEUES = {"retrieve": {"exchange": "default", "exchange_type": "direct", "routing_key": "retrieve"},
                 "process": {"exchange": "default", "exchange_type": "direct", "routing_key": "process "},
                 "celery": {"exchange": "default", "exchange_type": "direct", "routing_key": "celery"}}

class MyRouter(object):

    def route_for_task(self, task, args=None, kwargs=None):
        if task == "app.tasks.retrieve_page":
            return { "queue": "retrieve" }
        else:
            return { "queue": "process" }

CELERY_ROUTES = (MyRouter(), )

MAX_CORPUS_SIZE = 500
SEED_URL = "http://techcrunch.com/startups/"