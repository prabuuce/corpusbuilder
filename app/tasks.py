from app import app, celery
import requests
from app.page.models import Page
from app.extraction.models import Extraction
#from app.extraction.boilerpipe_wrapper import BoilerpipeExtraction

pagenotfound = lambda : {"message":"Page not Found", "status":400}
extractionnotfound = lambda : {"message":"Extraction not Found", "status":400}

@celery.task
def retrieve_page(url, add_if_not_found=True):
    print "retrieving Page for ....%s" % (url)
    with app.test_request_context('/'): # this is to adjust for the fact that we are in celery content and not Flask context 
        app.preprocess_request()
    page = Page.get_page_by_url(url)
    if page is None:
        if add_if_not_found: # add a page
            page = Page.add_page(url)
        else: # just return
            return pagenotfound()
    else:
        pass # do nothing
    find_links.delay(page.id)
    
    #retrieve_extraction.delay(page.id)
    # The reason this was commented was because boilerpipe_extract_and_populate task was getting overwhelmed
    # because the page population was growing so fast.
    # New approach: First populate 1000 pages. The stop page population and start the extraction process
    
    #Using Rest API
    ''''r = requests.get("http://127.0.0.1:5000/pages", params={"url":url})
    if r.text == u"400\n": # Page not found
        if add_if_not_found: # time to add a new Page document
            r = requests.post("http://127.0.0.1:5000/pages", params={"url":url})
        else: # do nothing
            return
    page_id = r.json()["_id"]'''

@celery.task
def retrieve_extraction(page_id,add_if_not_found=True):
    print "retrieving Extraction for ....%s" % (page_id)
    with app.test_request_context('/'): # this is to adjust for the fact that we are in celery content and not Flask context 
        app.preprocess_request()
    extraction = Extraction.get_extraction_by_page_id(page_id)
    if extraction is None:
        if add_if_not_found: # add a page
            extraction = Extraction.add_extraction(page_id)
        else:
            return extractionnotfound
    else:
        pass # do nothing
    boilerpipe_extract_and_populate.delay(page_id,extraction.id)
    
    #Using Rest API
    '''rExt = requests.get("http://127.0.0.1:5000/extractions", params={"page_id":page_id})
    if rExt.text == u"400\n": # Extraction not found
        if add_if_not_found: # time to add a new Extraction document
            rExt = requests.post("http://127.0.0.1:5000/extractions", params={"page_id":page_id})
            ext_id = rExt.json()["_id"] # _id of the newly added Extraction
            assert ext_id is not None
            # now do the boilerplate-sans content extraction for the new Extraction in a separate task
            boilerpipe_extract_and_populate.delay(page_id,ext_id)'''

@celery.task
def boilerpipe_extract_and_populate(page_id, ext_id):
    print "extracting using boilerpipe..."
    
    # For some reason this approach of directly calling the static method is not working
    '''with app.test_request_context('/'): # this is to adjust for the fact that we are in celery content and not Flask context 
        app.preprocess_request()
    BoilerpipeExtraction.extract_content(page_id, ext_id)'''
    
    # Therefore, switching to calling the REST API. This seems to be working 
    #Using Rest API
    return requests.get("http://127.0.0.1:5000/extractions/bp/%s,%s"%(page_id,ext_id))

@celery.task
def find_links(page_id):
    with app.test_request_context('/'): # this is to adjust for the fact that we are in celery content and not Flask context 
        app.preprocess_request()
    page = Page.find_links(page_id)
    if page is None: return pagenotfound()
    for link in page.links:
        retrieve_page.delay(link)

    

    
    