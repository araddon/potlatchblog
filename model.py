from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext.db import Model as DBModel
from datetime import datetime

from demisaucepy.django_helper import AggregatorMeta
from demisaucepy.declarative import has_a, has_many, \
    aggregator_callable, make_declarative
from demisaucepy import cfg




cfg.CFG['demisauce.apikey'] = '173726158347a26b3836d1c6c09e6c646461517a'
cfg.CFG['demisauce.url'] = 'http://localhost:4951'
cfg.CFG['demisauce.appname'] = 'djangodemo'

class BaseModel(db.Model):
    def __init__(self, parent=None, key_name=None, _app=None, **kwds):
        self.__isdirty = False
        DBModel.__init__(self, parent=None, key_name=None, _app=None, **kwds)
    
    def __setattr__(self,attrname,value):
        """
        DataStore api stores all prop values say "email" is stored in "_email" so
        we intercept the set attribute, see if it has changed, then check for an
        onchanged method for that property to call
        """
        if (attrname.find('_') != 0):
            if hasattr(self,'_' + attrname):
                curval = getattr(self,'_' + attrname)
                if curval != value:
                    self.__isdirty = True
                    if hasattr(self,attrname + '_onchange'):
                        getattr(self,attrname + '_onchange')(curval,value)
        
        DBModel.__setattr__(self,attrname,value)
    

class GAEMeta(BaseModel,AggregatorMeta): pass

class Cache(db.Model):
    cachekey = db.StringProperty(multiline=False)
    content = db.TextProperty()

class Blog(db.Model):
    owner = db.UserProperty()
    description = db.TextProperty()
    baseurl = db.StringProperty(multiline=False,default='http://yourapp.appspot.com')
    urlpath = db.StringProperty(multiline=False)
    title = db.StringProperty(multiline=False)
    subtitle = db.StringProperty(multiline=False)
    entrycount = db.IntegerProperty(default=0)
    feedurl = db.StringProperty(multiline=False,default='http://feeds.feedburner.com/yoursitesname')
    blogversion = db.StringProperty(multiline=False,default='1.15')
    layout = db.StringProperty(multiline=False,default='2cola',choices=[
        '3cola', '3colb', '2cola','2colb'])
    theme = db.StringProperty(multiline=False,default='freshpress.css')
    area1 = db.TextProperty(default='')
    area2 = db.TextProperty(default='')
    area3 = db.TextProperty(default='')
    sidebar = db.TextProperty(default='')
    topmenu = db.StringProperty(multiline=True,default='')
    archivehtml = db.TextProperty(default='')
    tags = db.TextProperty(default='{}')
    analyticsjs = db.TextProperty(default='')
    commentjs = db.TextProperty(default='')
    
    def save(self):
        self.put()
    
    def initialsetup(self):
        self.title = 'Your Blog Title'
        self.subtitle = 'Your Blog Subtitle'
        self.area1 = '<h3>Lower Left Title</h3>\nContent in lower left'
        self.area2 = '<h3>Center Bottom Box</h3>\nContent in center footer'
        self.area3 = '<h3>Right Footer</h3>\nContent in footer right'
    

class Archive(db.Model):
    blog = db.ReferenceProperty(Blog)
    monthyear = db.StringProperty(multiline=False)
    """March-08"""
    entrycount = db.IntegerProperty(default=0)
    date = db.DateTimeProperty(auto_now_add=True)

class Tag(db.Model):
    blog = db.ReferenceProperty(Blog)
    tag = db.StringProperty(multiline=False)
    tagcount = db.IntegerProperty(default=0)

class Link(db.Model):
    blog = db.ReferenceProperty(Blog)
    href = db.StringProperty(multiline=False,default='')
    linktype = db.StringProperty(multiline=False,default='blogroll')
    linktext = db.StringProperty(multiline=False,default='')

class Entry(BaseModel):
    #__metaclass__ = GAEMeta
    author = db.UserProperty()
    blog = db.ReferenceProperty(Blog)
    published = db.BooleanProperty(default=False)
    content = db.TextProperty(default='')
    title = db.StringProperty(multiline=False,default='')
    date = db.DateTimeProperty(auto_now_add=True)
    tags = db.ListProperty(db.Category)
    slug = db.StringProperty(multiline=False,default='')
    monthyear = db.StringProperty(multiline=False)
    entrytype = db.StringProperty(multiline=False,default='post',choices=[
        'post','page'])
    commentcount = db.IntegerProperty(default=0)
    comments = has_many(name='comment',lazy=True,local_key='slug' )
    phphello = has_a(name='helloworld',app='phpdemo',lazy=True,local_key='slug' )
    
    def published_onchange(self,curval,newval):
        if self.entrytype == 'post':
            my = self.date.strftime('%b-%Y') # May-2008
            archive = Archive.all().filter('monthyear',my).fetch(10)
            if curval == False and newval == True:
                # add to archive
                if archive == []: # new month
                    archive = Archive(blog=self.blog,monthyear=my)
                else: 
                    archive = archive[0]
                archive.entrycount += 1
                archive.put()
                self.blog.entrycount += 1
            else:
                # remove from archive
                if archive and archive[0]:
                    archive = archive[0]
                    archive.entrycount -= 1
                    if archive.entrycount == 0:
                        archive.delete()
                    else:
                        archive.put()
                self.blog.entrycount -= 1
            
            self.blog.save()
    
    def get_tags(self):
        '''comma delimted list of tags'''
        return ','.join([tag for tag in self.tags])
    
    def set_tags(self, tags):
        if tags:
            tagstemp = [db.Category(tag.strip()) for tag in tags.split(',')]
            self.tagsnew = [tag for tag in tagstemp if not tag in self.tags]
            self.tags = tagstemp
    
    tagswcommas = property(get_tags,set_tags)
    
    def update_archive(self):
        """Checks to see if there is a month-year entry for the
        month of current blog, if not creates it and increments count"""
        my = self.date.strftime('%b-%Y') # May-2008
        archive = Archive.all().filter('monthyear',my).fetch(10)
        if self.entrytype == 'post':
            if archive == []:
                archive = Archive(blog=self.blog,monthyear=my)
                self.monthyear = my
                archive.put()
            else:
                # ratchet up the count
                archive[0].entrycount += 1
                archive[0].put()
        
    
    def update_tags(self):
        """Update Tag cloud info"""
        #b = self.blog
        #print b.tags
        #for tag in self.tagsnew:
        #    if not b.tags.has_key(tag):
        #        b.tags.update({tag:1})
        #    else:
        #        b.tags.update({tag:b.tags[tag]+1})
        pass
    
    def save(self):
        """
        Use this instead of self.put(), as we do some other work here
        """
        #TODO for each tag ensure it has a tag
        self.update_tags()
        my = self.date.strftime('%b-%Y') # May-2008
        self.monthyear = my
        self.put()
    
    @classmethod
    def allpublished(cls,type='post'):
        return Entry.all().filter('entrytype =',type
            ).filter("published =", True).order('-date')
    
make_declarative(Entry.__dict__)
for attr in Entry.__dict__.keys():
    print 'attr %s, %s' % (attr,Entry.__dict__[attr])
