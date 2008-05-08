from google.appengine.api import users
#from google.appengine.ext import webapp
from google.appengine.ext import db


class Cache(db.Model):
    cachekey = db.StringProperty(multiline=False)
    content = db.TextProperty()

class Tag(db.Model):
    author = db.UserProperty()
    tag = db.StringProperty(multiline=False)
    date = db.DateTimeProperty(auto_now_add=True)

class Blog(db.Model):
    owner = db.UserProperty()
    description = db.TextProperty()
    baseurl = db.StringProperty(multiline=False,default='http://yourapp.appspot.com')
    urlpath = db.StringProperty(multiline=False)
    date = db.DateTimeProperty(auto_now_add=True)
    tags = db.ListProperty(db.Category)
    title = db.StringProperty(multiline=False)
    subtitle = db.StringProperty(multiline=False)
    layout = db.StringProperty(multiline=False,default='2cola',choices=[
        '3cola', '3colb', '2cola','2colb'])
    area1 = db.TextProperty(default='')
    area2 = db.TextProperty(default='')
    area3 = db.TextProperty(default='')

class Link(db.Model):
    blog = db.ReferenceProperty(Blog)
    href = db.StringProperty(multiline=False,default='')
    linktype = db.StringProperty(multiline=False,default='blogroll')
    linktext = db.StringProperty(multiline=False,default='')

class Entry(db.Model):
    author = db.UserProperty()
    content = db.TextProperty(default='')
    title = db.StringProperty(multiline=False,default='')
    date = db.DateTimeProperty(auto_now_add=True)
    tags = db.ListProperty(db.Category)
    slug = db.StringProperty(multiline=False,default='')
    entrytype = db.StringProperty(multiline=False,default='post',choices=[
        'post','page'])
    
    def get_tags(self):
        '''comma delimted list of tags'''
        return ','.join([tag for tag in self.tags])
    def set_tags(self, tags):
        self.tags = [db.Category(tag.strip()) for tag in tags.split(',')]
    tagswcommas = property(get_tags,set_tags)
    
    def save(self):
        #TODO for each tag ensure it has a tag
        self.put()
