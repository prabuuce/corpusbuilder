from flaskext.couchdb import Document, TextField, ViewDefinition, DateTimeField
from app.page.models import Page
from app import app, api, parser, manager
from datetime import datetime
from flask_restful import Resource

class Extraction(Document):
    type = TextField(default="extraction")
    page_id = TextField()
    bp_content = TextField()
    jt_content = TextField()
    last_checked = DateTimeField(default=datetime.now)
    
    #http://127.0.0.1:5984/<db>/_design/extraction/_view/all
    all_extractions = ViewDefinition('extraction', 'all','''\
            function (doc) {
                if(doc.type == "extraction") {
                    emit(null, doc._id);
                }
            }''')
    
    #http://127.0.0.1:5984/<db>/_design/extraction/_view/by_page_id
    extraction_by_page_id = ViewDefinition('extraction', 'by_page_id','''\
            function (doc) {
                if(doc.type == "extraction") {
                    emit(doc.page_id, doc._id);
                }
            }''')
    
    def update(self, bp_content="", jt_content=""):
        # looks at the page_id, gets the page's contents and uses boilerplate extraction on the content
        page = Page.load(self.page_id)
        assert page is not None
        self.bp_content = bp_content
        self.jt_content = jt_content
        self.last_checked = datetime.now()
        self.store()
        return self
    
    @staticmethod # return a Extraction object
    def add_extraction(page_id):
        extraction = Extraction(page_id=page_id) # create the extraction
        return extraction.update() # the update function will take care of populating and storing the object  
    
    @staticmethod # returns a Extraction object
    def get_extraction(_id):
        return Extraction.load(_id)
    
    @staticmethod # returns a list of Page objects
    def get_all_extractions():
        all_exes=[]
        for row in Extraction.all_extractions():
            all_exes.append(Extraction.load(row.id))
        return all_exes
    
    @staticmethod # returns a Extraction object given a page_id
    def get_extraction_by_page_id(page_id):
        if len(Extraction.extraction_by_page_id(key=page_id)) > 0:
            return Extraction.load(Extraction.extraction_by_page_id(key=page_id).rows[0].id)
        else:
            return None
    
class ExtractionAPI(Resource):
    #curl http://localhost:5000/extractions/<_id>
    def get(self, _id):
        retval = lambda x: x._to_json(x.id) if x else 400
        return retval(Extraction.get_extraction(_id))
    
    # curl http://localhost:5000/<_id> -d "bp_content=<String: long text>" -X PUT
    # curl http://localhost:5000/<_id> -d "jt_content=<String: long text>" -X PUT
    def put(self, _id):
        retval = lambda x: x._to_json(x.id) if x else 400
        args = parser.parse_args()
        bp_content = args['bp_content']
        if bp_content is not None:
            extraction = Extraction.get_extraction(_id)
            assert extraction is not None
            return retval(extraction.update(bp_content=bp_content))
        jt_content = args['jt_content']
        if jt_content is not None:
            extraction = Extraction.get_extraction(_id)
            assert extraction is not None
            return retval(extraction.update(jt_content=jt_content))

class ExtractionListAPI(Resource):
    #curl http://localhost:5000/extractions
    #curl http://localhost:5000/extractions?"<page_id>"
    def get(self): # returns all Extractions, or returns a specific Extractions based on page_id
        args = parser.parse_args()
        page_id = args['page_id']
        if page_id is None or "": # requested all Extractions
            jsonify = lambda x: x._to_json(x.id) if x else {}
            return map(jsonify, Extraction.get_all_extractions()) 
        else: # requested Extractions filtered by one page_id
            retval = lambda x: x._to_json(x.id) if x else 400
            return retval(Extraction.get_extraction_by_page_id(page_id))

    # curl http://localhost:5000/pages -d "url=http://www.bbc.com" -X POST -v
    def post(self): # creates a new page
        args = parser.parse_args()
        page_id = args['page_id']
        if page_id is None or "":
            return 400 # bad request
        retval = lambda x: x._to_json(x.id) if x else 400
        return retval(Extraction.add_extraction(page_id))
    
manager.add_document(Extraction)
manager.add_viewdef(Extraction.all_extractions)
manager.add_viewdef(Extraction.extraction_by_page_id)
manager.sync(app)

api.add_resource(ExtractionAPI, '/extractions/<string:_id>')
api.add_resource(ExtractionListAPI, '/extractions')
