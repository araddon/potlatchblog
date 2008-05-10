import cgi, os
from functools import wraps
import wsgiref.handlers

from google.appengine.ext.webapp import template
from google.appengine.api import users
import webapp as webapp2
from google.appengine.ext import webapp
from google.appengine.ext import db

from model import *

def requires_admin(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
            return
            raise self.error(403)
        elif not users.is_current_user_admin():
            #self.response.clear()
            #self.response.set_status(403).
            self.error(403)
            template_vals = {'entries': None,'message':'This User does not have priveleges to the Admin Section'}
            self.render('views/error.html',template_vals) 
        else:
            return method(self, *args, **kwargs)
    return wrapper
    
def printinfo(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        print self #.__name__
        print dir(self)
        for x in self.__dict__:
            print x
        return method(self, *args, **kwargs)
    return wrapper
    


class BaseController(webapp2.RequestHandler):
    def __init__(self):
        self.template = 'index.html'
        self.blog = Blog.all().fetch(1)
        if self.blog == []:
            pass
        else:
            self.blog = self.blog[0]
        self.template_vals = {}
    
    def __before__(self,*args):
        pass
    
    def __after__(self,*args):
        pass
    
    def render(self,template_file,template_vals):
        """
        Helper method to render the appropriate template
        """
        if self.blog == None and self.request.path != "/admin/setup":
            # no blog configured
            self.redirect('/admin/setup')
        
        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
        
        template_vals.update({'url':url,
                         'url_linktext':url_linktext,
                         'blog':self.blog
                         })
        template_vals.update(self.template_vals)
        path = os.path.join(os.path.dirname(__file__), template_file)
        self.response.out.write(template.render(path, template_vals))
    

class BasePublicPage(BaseController):
    """
    Do all the common public page prep such as nav pages etc
    """
    def __before__(self,slug=None):
        pages = Entry.all().filter("entrytype =", "page").fetch(20)
        recententries = Entry.all().filter('entrytype =','post').order('-date').fetch(10)
        #links = Link.all().filter("linktype =", "blogroll").fetch(20)
        links = Link.all().filter('linktype =','blogroll')
        self.template_vals.update({'recententries':recententries,
            'pages':pages,'links':links})
    

class MainPage(BasePublicPage):
    #@printinfo
    def get(self,url_part1=None,url_part2=None):
        #entries = Entry.all().filter("tags =", "none").order('-date')
        entries = []
        if url_part2 == None and url_part1 == None:
            entries = Entry.all().filter('entrytype =','post').order('-date').fetch(10)
        elif url_part2 == None:
            entries = Entry.all().filter('slug', url_part1)
        else:
            entries = db.GqlQuery("SELECT * FROM Entry WHERE slug = :1", url_part2)
        
        self.render('views/index.html',{'entries':entries})
    

class PublicPage(BasePublicPage):
    def get(self,slug=None):
        entries = db.GqlQuery("SELECT * FROM Entry WHERE slug = :1", slug)
        self.render('views/page.html',{'entries':entries})
    

class TagPage(BasePublicPage):
    def get(self,tags=None):
        entries = Entry.all().filter("tags =", tags).filter('entrytype =','post').order('-date')
        self.render('views/index.html',{'entries':entries})
    

class FeedHandler(BaseController):
    def get(self,tags=None):
        entries = Entry.all().filter('entrytype =','post').order('-date').fetch(10)
        self.response.headers['Content-Type'] = 'application/atom+xml'
        self.render('views/atom.xml',{'entries':entries})
    

class AdminConfig(BaseController):
    @requires_admin
    def get(self):
        blogedit = Blog.all().fetch(1)
        #blog = Blog.all()
        if blogedit:
            blogedit = blogedit[0]
        else:
            blogedit = Blog()
            blogedit.save()
            blogedit.initialsetup()
        self.render('views/setup.html',{'blogedit':blogedit,'blogclass':Blog})
    
    @requires_admin
    def post(self):
        key = self.request.get('object_key')
        if key == None or key == '': #new
            blog = Blog()
        else: # edit
            blog = db.get(db.Key(key))
            if users.get_current_user():
                blog.owner = users.get_current_user()
        
        blog.description = self.request.get('description')
        blog.title = self.request.get('title')
        blog.subtitle = self.request.get('subtitle')
        blog.layout = self.request.get('layout')
        blog.baseurl = self.request.get('baseurl')
        blog.area1 = self.request.get('area1')
        blog.area2 = self.request.get('area2')
        blog.area3 = self.request.get('area3')
        blog.save()
        self.redirect('/admin/entry/list/post')
    

class AdminEntry(BaseController):
    @requires_admin
    def get(self,entrytype='post',key=None):
        entry = None
        if key == None or key == '':
            entry = Entry()
            entry.entrytype = entrytype
        else:
            entry = db.get(db.Key(key))
        
        self.render('views/admin.html',{'entry':entry,'entries':[]})
    
    @requires_admin
    def post(self,entrytype='post',key=None):
        entry = None
        if key == None or key == '':
            entry = Entry(blog=self.blog)
            entry.entrytype = self.request.get('entrytype')
        else:
            entry = db.get(db.Key(key))
        
        if users.get_current_user():
            entry.author = users.get_current_user()
        
        entry.content = self.request.get('content')
        entry.title = self.request.get('title')
        entry.slug = self.request.get('real_permalink')
        entry.tagswcommas = self.request.get('tags')
        entry.save()
        self.redirect('/admin/entry/list/%s' % entry.entrytype )
    

class AdminList(BaseController):
    @requires_admin
    def get(self,entrytype='post',template_vals={}):
        entries = Entry.all().filter('entrytype =',entrytype)
        self.render('views/admin.html',{'entries':entries})
    

class AdminLinks(BaseController):
    @requires_admin
    def get(self,linktype='blogroll'):
        links = Link.all()#.filter('linktype =',linktype)
        link = Link(href='',linktext='',linktype='blogroll')
        self.render('views/linkadmin.html',{'entries':None,'links':links,
            "link":link})
    
    @requires_admin
    def post(self,linktype='blogroll',key=None):
        link = None
        if key == None or key == '':
            link = Link(blog=self.blog)
        else:
            link = db.get(db.Key(key))
        
        link.linktext = self.request.get('linktext')
        link.href = self.request.get('title')
        link.put()
        self.response.out.write('link %s added' % link.linktype)
    

def main():
    application = webapp2.WSGIApplication2(
                    [('/', MainPage),
                     ('/admin/entry/list/(.*)', AdminList),
                     ('/admin/entry/(.*)/(.*)', AdminEntry),
                     ('/admin/entry/(.*)', AdminEntry),
                     ('/admin/links/(.*)', AdminLinks),
                     ('/admin/setup', AdminConfig),
                     ('/tag/(.*)', TagPage),
                     ('/atom', FeedHandler),
                     (r'/page/(.*)', PublicPage),
                     (r'/entry/(.*)', MainPage),
                     (r'/b/(.*)/(.*)', MainPage),
                     ],debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
    main()