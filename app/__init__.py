from flask import Flask
from flaskext.couchdb import CouchDBManager
from flask_restful import Api, reqparse
from celery import Celery

## configure app
app = Flask(__name__)
app.config.from_pyfile('%s/settings.py' % app.root_path)

## configure Flask-CouchDB
manager = CouchDBManager()
manager.setup(app)

## configure Flask-Restful
api = Api(app)
parser = reqparse.RequestParser()
parser.add_argument('url', type=str)
parser.add_argument('page_id', type=str)
parser.add_argument('ext_id', type=str)
parser.add_argument('bp_content', type=str)
parser.add_argument('jt_content', type=str)

def make_celery():
    celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery

celery = make_celery()

from app.page import models as page_models
from app.extraction import models as extraction_models
from app.extraction import boilerpipe_wrapper
import views




