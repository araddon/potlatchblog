from google.appengine.api import users
#from google.appengine.ext import webapp
from google.appengine.ext import db


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
    layout = db.StringProperty(multiline=False,default='2cola',choices=[
        '3cola', '3colb', '2cola','2colb'])
    area1 = db.TextProperty(default='')
    area2 = db.TextProperty(default='')
    area3 = db.TextProperty(default='')
    tags = db.TextProperty(default='{}')
    analyticsjs = db.StringProperty(multiline=True,default='')
    
    def save(self):
        self.put()
    
    def initialsetup(self):
        self.title = 'Your Blog Title'
        self.subtitle = 'Your Blog Subtitle'
        self.area1 = '<h3>Lower Left Title</h3>\nContent in lower left'
        self.area2 = '<h3>Center Bottom Box</h3>\nContent in center footer'
        self.area3 = '<h3>Right Footer</h3>\nContent in footer right'
    

class Tag(db.Model):
    blog = db.ReferenceProperty(Blog)
    tag = db.StringProperty(multiline=False)
    tagcount = db.IntegerProperty(default=0)

class Link(db.Model):
    blog = db.ReferenceProperty(Blog)
    href = db.StringProperty(multiline=False,default='')
    linktype = db.StringProperty(multiline=False,default='blogroll')
    linktext = db.StringProperty(multiline=False,default='')

class Entry(db.Model):
    author = db.UserProperty()
    blog = db.ReferenceProperty(Blog)
    content = db.TextProperty(default='')
    title = db.StringProperty(multiline=False,default='')
    date = db.DateTimeProperty(auto_now_add=True)
    tags = db.ListProperty(db.Category)
    slug = db.StringProperty(multiline=False,default='')
    entrytype = db.StringProperty(multiline=False,default='post',choices=[
        'post','page'])
    commentcount = db.IntegerProperty(default=0)
    
    def get_tags(self):
        '''comma delimted list of tags'''
        return ','.join([tag for tag in self.tags])
    
    def set_tags(self, tags):
        if tags:
            tagstemp = [db.Category(tag.strip()) for tag in tags.split(',')]
            self.tagsnew = [tag for tag in tagstemp if not tag in self.tags]
            self.tags = tagstemp
    
    tagswcommas = property(get_tags,set_tags)
    
    def save(self):
        """
        Use this instead of self.put(), as we do some other work here
        """
        #TODO for each tag ensure it has a tag
        
        # update # entry count if new
        if not self.is_saved():
            self.blog.entrycount += 1
            self.blog.save()
        #b = self.blog
        #print b.tags
        #for tag in self.tagsnew:
        #    if not b.tags.has_key(tag):
        #        b.tags.update({tag:1})
        #    else:
        #        b.tags.update({tag:b.tags[tag]+1})
        self.put()
    

