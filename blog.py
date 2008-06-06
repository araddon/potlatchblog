import cgi, os
from functools import wraps
import wsgiref.handlers

from google.appengine.ext.webapp import template, \
    WSGIApplication
from google.appengine.api import users
import webapp as webapp2
from google.appengine.ext import webapp
from google.appengine.ext import db

from model import *

def rebuild_cache(blog):
    """
    Pre-Render's and cache's html in blog object.  Everything
    in here doesn't change very often, so we can update it at point of change
    """
    pages = Entry.all().filter("entrytype =", "page").filter("published =", True).fetch(20)
    archives = Archive.all().order('-date').fetch(10)
    recententries = Entry.all().filter('entrytype =','post').filter("published", True).order('-date').fetch(10)
    links = Link.all().filter('linktype =','blogroll')
    template_vals = {'recententries':recententries,'pages':pages,
            'links':links,'archives':archives}
            
    path = os.path.join(os.path.dirname(__file__), 'views/sidebar.html')
    blog.sidebar = template.render(path, template_vals)
    path = os.path.join(os.path.dirname(__file__), 'views/topmenu.html')
    blog.topmenu = template.render(path, template_vals) 
    blog.save()

def requires_admin(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
            return
            raise self.error(403)
        elif not users.is_current_user_admin():
            return self.error(403)
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
        current_userisadmin = False
        if users.get_current_user() and users.is_current_user_admin():
            current_userisadmin = True
        self.template_vals = {'current_userisadmin':current_userisadmin}
    
    def __before__(self,*args):
        pass
    
    def __after__(self,*args):
        pass
    
    def error(self,errorcode,message='an error occured'):
        if errorcode == 404:
            message = 'Sorry, we were not able to find the requested page.  We have logged this error and will look into it.'
        elif errorcode == 403:
            message = 'Sorry, that page is reserved for administrators.  '
        elif errorcode == 500:
            message = "Sorry, the server encountered an error.  We have logged this error and will look into it."
        return self.render('views/error.html',{'message':message})
    
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
        
        self.template_vals.update({'url':url,
                         'url_linktext':url_linktext,
                         'blog':self.blog
                         })
        self.template_vals.update(template_vals)
        path = os.path.join(os.path.dirname(__file__), template_file)
        self.response.out.write(template.render(path, self.template_vals))
    

class BasePublicPage(BaseController):
    """
    Do all the common public page prep such as nav pages etc
    """
    def __before__(self,slug=None):
        #self.template_vals.update(public_page_gets())
        pass
    

class MainPage(BasePublicPage):
    #@printinfo
    def get(self,slug=None):
        entries = []
        if slug == None:
            entries = Entry.all().filter('entrytype =','post').\
                filter("published =", True).order('-date').fetch(10)
        else:
            entries = Entry.all().filter('slug', slug).fetch(1)
            if not entries or len(entries) == 0:
                return self.error(404)
            
        
        self.render('views/index.html',{'entries':entries,'slug':slug})
    

class PublicPage(BasePublicPage):
    def get(self,slug=None):
        entries = Entry.all().filter('slug', slug).filter("published =", True)
        self.render('views/page.html',{'entries':entries})
    

class ArchivePage(BasePublicPage):
    def get(self,monthyear=None):
        entries = Entry.all().filter('monthyear', monthyear).\
            filter("published =", True).filter('entrytype','post').order('-date')
        self.render('views/index.html',{'entries':entries})
    

class TagPage(BasePublicPage):
    def get(self,tags=None):
        entries = Entry.all().filter("tags =", tags).filter('entrytype =','post').order('-date')
        self.render('views/index.html',{'entries':entries})
    

class FeedHandler(BaseController):
    def get(self,tags=None):
        entries = Entry.all().filter('entrytype =','post').order('-date').fetch(10)
        if entries and entries[0]:
            last_updated = entries[0].date
            last_updated = last_updated.strftime("%Y-%m-%dT%H:%M:%SZ") 
        for e in entries:
            e.formatted_date = e.date.strftime("%Y-%m-%dT%H:%M:%SZ") 
        self.response.headers['Content-Type'] = 'application/atom+xml'
        self.render('views/atom.xml',{'entries':entries,'last_updated':last_updated})
    

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
        self.render('views/setup.html',{'blog':blogedit,'blogclass':Blog})
    
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
        blog.feedurl = self.request.get('feedurl')
        blog.area1 = self.request.get('area1')
        blog.area2 = self.request.get('area2')
        blog.area3 = self.request.get('area3')
        blog.analyticsjs = self.request.get('analyticsjs')
        blog.commentjs = self.request.get('commentjs')
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
        entry.published = bool(int(self.request.get('published')))
        entry.title = self.request.get('title')
        entry.slug = self.request.get('real_permalink')
        entry.tagswcommas = self.request.get('tags')
        entry.save()
        rebuild_cache(self.blog)
        self.redirect('/admin/entry/list/%s' % entry.entrytype )
    
    @requires_admin
    def delete(self,key=None):
        entry = None
        if key == None or key == '':
            print 'whoops'
        else:
            entry = db.get(db.Key(key))
            entry.delete()
        rebuild_cache(self.blog)
    

class AdminList(BaseController):
    @requires_admin
    def get(self,entrytype='post',template_vals={}):
        entries = Entry.all().filter('entrytype =',entrytype).order('-date')
        self.render('views/admin.html',{'entries':entries})
    

class AdminMigrate(BaseController):
    @requires_admin
    def get(self,to_version='1.15'):
        if to_version == '999.99':
            pass
        elif to_version == '1.18':
            archives = Archive.all()
            for a in archives:
                a.delete()
            entries = Entry.all().filter('entrytype =','post').filter('published',True)
            for e in entries:
                e.published = False
                e.save()
            self.blog.entrycount = 0 # reset to start migration
            self.blog.put()
            for e in entries:
                e.published = True
                e.save()
                print 'update to %s' % (e.monthyear)
            self.blog.blogversion = to_version
            self.blog.put()
        elif to_version == '1.17':
            links = Link.all()
            for l in links:
                l.delete()
        elif to_version == '1.16':
            archives = Archive.all()
            for a in archives:
                a.delete()
            entries = Entry.all().filter('entrytype =','post')
            self.blog.entrycount = 0 # reset to start migration
            for e in entries:
                e.update_archive()
                e.monthyear = e.date.strftime('%b-%Y')
                self.blog.entrycount += 1
                e.put()
                print 'update to %s' % (e.monthyear)
            archive = Archive.all()
            self.blog.blogversion = to_version
            self.blog.put()
        
    


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
        link.href = self.request.get('href')
        link.put()
        rebuild_cache(self.blog)
        self.response.out.write('link %s added' % link.linktype)
    

def main():
    application = webapp2.WSGIApplication2(
                    [('/', MainPage),
                     ('/admin', AdminList),('/admin/', AdminList),
                     ('/admin/entry/list/(.*)', AdminList),
                     ('/admin/entry/(.*)/(.*)', AdminEntry),
                     ('/admin/entry/(.*)', AdminEntry),
                     ('/admin/links/(.*)', AdminLinks),
                     ('/admin/setup', AdminConfig),
                     ('/admin/migrate/(.*)', AdminMigrate),
                     ('/tag/(.*)', TagPage),
                     ('/atom', FeedHandler),
                     (r'/page/(.*)', PublicPage),
                     (r'/archive/(.*)', ArchivePage),
                     (r'/entry/(.*)', MainPage),
                     ],debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
    main()