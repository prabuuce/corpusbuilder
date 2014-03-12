from flask_restful import Resource, abort 
from boilerpipe.extract import Extractor, jpype
from app import api
from app.page.models import Page
from app.extraction.models import Extraction

badrequest = lambda : {"message":"Bad Request", "status":400}
documentnotfound = lambda : {"message":"Doc not Found", "status":400}
nocontent = lambda : {"message":"No Content", "status":400}
success = lambda : {"message":"Success", "status":200}

class BoilerpipeExtraction(Resource):
    
    @staticmethod
    def extract_content(page_id, ext_id, htmlReturn=False): # htmlReturn=False: by default returns text content
        if (page_id is None or "") or (ext_id is None or ""): return badrequest()
        page = Page.get_page(page_id)
        if page is None: return documentnotfound()
        extraction = Extraction.get_extraction(ext_id)
        if extraction is None: return documentnotfound()
        original_content = page.content
        if original_content is None or original_content is "": return nocontent()
        
        if not jpype.isThreadAttachedToJVM():
            jpype.attachThreadToJVM()
        extractor = Extractor(extractor='DefaultExtractor', html=original_content)
        if not htmlReturn:
            bp_content = extractor.getText()
        else:
            bp_content = extractor.getHTML()
        if bp_content is None: nocontent()
        
        extraction.update(bp_content=bp_content)
        return success()
        
    
    #curl http://localhost:5000/extractions/bp/<string:page_id>,<string:ext_id>
    #e.g. curl http://localhost:5000/extractions/bp/123,456
    def get(self, page_id, ext_id):
        return BoilerpipeExtraction.extract_content(page_id, ext_id)

api.add_resource(BoilerpipeExtraction, '/extractions/bp/<string:page_id>,<string:ext_id>')
