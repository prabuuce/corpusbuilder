from flaskext.couchdb import Document, TextField, ViewDefinition, DateTimeField, ListField
from app import app, manager, api, parser
from flask_restful import Resource
from robotparser import RobotFileParser
import pickle, base64, time
from datetime import datetime
from urlparse import urlparse
from urllib2 import urlopen, Request
import re, htmlentitydefs

pagenotfound = lambda : {"message":"Page not Found", "status":400}

class Page(Document):
    type = TextField(default="page")
    url = TextField()
    content = TextField()
    links = ListField(TextField())
    last_checked = DateTimeField(default=datetime.now)
    
    #http://127.0.0.1:5984/pycrawlerdb/_design/page/_view/by_url
    all_pages = ViewDefinition('page', 'all','''\
            function (doc) {
                if(doc.type == "page") {
                    emit(null, doc._id);
                }
            }''')
    
    #http://127.0.0.1:5984/pycrawlerdb/_design/page/_view/by_url
    page_by_url = ViewDefinition('page', 'by_url','''\
            function (doc) {
                if(doc.type == "page") {
                    emit(doc.url, doc._id);
                }
            }''')
    
    def update(self):
        # first check with RobotsTxt if allowed to crawl or not
        parse = urlparse(self.url)
        robotstxt = RobotsTxt.get_by_domain(parse.scheme, parse.netloc)
        if not robotstxt.is_allowed(self.url): # no crawlers allowed
            return False
        # Next, get the content from URL
        req = Request(self.url, None, {"User-Agent": app.config['USER_AGENT'] })
        resp = urlopen(req)
        if not resp.info()["Content-Type"].startswith("text/html"):
            return False
        self.content = resp.read().decode("utf8")
        self.last_checked = datetime.now()
        self.store()
        return self
    
    @staticmethod # return a Page object
    def add_page(url):
        page = Page(url=url) # create the page
        return page.update() # the update function will take care of populating and storing the object
    
    @staticmethod # returns a Page object
    def get_page(_id):
        return Page.load(_id)
    
    @staticmethod # returns a list of Page objects
    def get_all_pages():
        all_pages=[]
        for row in Page.all_pages():
            all_pages.append(Page.load(row.id))
        return all_pages
    
    @staticmethod # returns total number of pages
    def get_total_num_of_pages():
        return len(Page.all_pages())
    
    @staticmethod # returns a Page object
    def get_page_by_url(url):
        if len(Page.page_by_url(key=url)) > 0:
            return Page.load(Page.page_by_url(key=url).rows[0].id)
        else:
            return None
    
    @staticmethod # return a Page object
    def find_links(page_id):
        page = Page.load(page_id)
        if page is None or page.content is None: return pagenotfound()
        link_single_re = re.compile(r"<a[^>]+href='([^']+)'")
        link_double_re = re.compile(r'<a[^>]+href="([^"]+)"')
        raw_links = []
        for match in link_single_re.finditer(page.content):
            raw_links.append(match.group(1))
        for match in link_double_re.finditer(page.content):
            raw_links.append(match.group(1))
        page.links = []
        for link in raw_links:
            if link.startswith("#"):
                continue
            elif link.startswith("http://") or link.startswith("https://"):
                pass
            elif link.startswith("/"):
                parse = urlparse(page["url"])
                link = parse.scheme + "://" + parse.netloc + link
            else:
                link = "/".join(page["url"].split("/")[:-1]) + "/" + link
            page.links.append(unescape(link.split("#")[0]))
        print "find_links %s -> %i" % (page.url, len(page.links))
        page.store()
        return page    
        
            
    
class PageAPI(Resource):
    #curl http://localhost:5000/pages/<_id>
    def get(self, _id):
        retval = lambda x: x._to_json(x.id) if x else 400
        return retval(Page.get_page(_id))

class PageListAPI(Resource):
    #curl http://localhost:5000/pages?"url=http://www.bbc.com"
    #curl http://localhost:5000/pages
    def get(self): # returns all pages, or returns a specific page based on URL
        args = parser.parse_args()
        url = args['url']
        if url is None or "": # requested all Pages
            jsonify = lambda x: x._to_json(x.id) if x else {}
            return map(jsonify, Page.get_all_pages()) 
        else: # requested Pages filtered by one url
            retval = lambda x: x._to_json(x.id) if x else 400
            return retval(Page.get_page_by_url(url))

    # curl http://localhost:5000/pages -d "url=http://www.bbc.com" -X POST -v
    def post(self): # creates a new page
        args = parser.parse_args()
        url = args['url']
        if url is None or "":
            return 400 # bad request
        retval = lambda x: x._to_json(x.id) if x else 200
        return retval(Page.add_page(url))

class RobotsTxt(Document):
    type = TextField(default="robotstxt")
    domain = TextField()
    protocol = TextField()
    robot_parser_pickle = TextField()
    
    #http://127.0.0.1:5984/pycrawlerdb/_design/robtxt/_view/by_domain
    robtxt_by_domian = ViewDefinition('robtxt', 'by_domain','''\
            function (doc) {
                if(doc.type == "robotstxt") {
                    emit([doc.protocol, doc.domain],doc._id);
                }
            }''', descending=True)
    
    def _get_robot_parser(self):
        if self.robot_parser_pickle is not None:
            return pickle.loads(base64.b64decode(self.robot_parser_pickle))
        else:
            parser = RobotFileParser()
            parser.set_url(self.protocol + "://" + self.domain + "/robots.txt")
            self.robot_parser = parser
            return parser
        
    def _set_robot_parser(self, parser):
        self.robot_parser_pickle = base64.b64encode(pickle.dumps(parser))
        
    robot_parser = property(_get_robot_parser, _set_robot_parser)

    def is_valid(self):
        return (time.time() - self.robot_parser.mtime()) < 7*24*60*60

    def is_allowed(self, url):
        return self.robot_parser.can_fetch(app.config['USER_AGENT'], url)

    def update(self):
        print "getting %s://%s/robots.txt" % (self.protocol, self.domain)
        parser = self.robot_parser
        parser.read()
        parser.modified()
        self.robot_parser = parser
        self.store()
        
    @staticmethod
    def get_by_domain(protocol, domain):
        r = RobotsTxt.robtxt_by_domian(key=[protocol, domain])
        if len(r) > 0: 
            # we have already crawled here and obtained RobotsTxt info. No need to request it again
            for row in r:
                doc = RobotsTxt.load(row.value)
                if doc.is_valid():
                    return doc
        else:
            # We are here for the first time, we need to get the RobotsTxt info and store it for current and future reference
            doc = RobotsTxt(protocol=protocol, domain=domain)
        doc.update()
        return doc
        
manager.add_document(Page)
manager.add_viewdef(Page.all_pages)
manager.add_viewdef(Page.page_by_url)
manager.add_document(RobotsTxt)
manager.add_viewdef(RobotsTxt.robtxt_by_domian)
manager.sync(app)

api.add_resource(PageAPI, '/pages/<string:_id>')
api.add_resource(PageListAPI, '/pages')

########### Helper functions #######
def unescape(text):
    """Removes HTML or XML character references and entities from a text string.
    keep &amp;, &gt;, &lt; in the source code.
    """
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                print "value error"
                pass
        else:
            # named entity
            try:
                if text[1:-1] == "amp":
                    text = "&amp;amp;"
                elif text[1:-1] == "gt":
                    text = "&amp;gt;"
                elif text[1:-1] == "lt":
                    text = "&amp;lt;"
                else:
                    print text[1:-1]
                    text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                print "keyerror"
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)

