import os
import urllib
import random

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

ENTER_PAGE_TEMPLATE = """\
    <form action="/enter?%s" method="post">
      <div>
        <label for="author">Author:</label>
        <input type="text" id="author" />
      </div>
      <div>
        <label for="title">Title:</label>
        <textarea id="title"></textarea>
      </div>
      <div><input type="submit" value="Enter book info"></div>
    </form>
    <hr>
    <form>Genre:
      <input value="%s" name="genre_name">
      <input type="submit" value="switch">
    </form>
    <a href="%s">%s</a>
  </body>
</html>
"""

DEFAULT_GENRE  = 'Non-fiction'
DEFAULT_AUTHOR = 'zzzzzzzzzzz'
DEFAULT_ERROR  = 'false'

# We set a parent key on the 'Greetings' to ensure that they are all
# in the same entity group. Queries across the single entity group
# will be consistent.  However, the write rate should be limited to
# ~1/second.

def genre_key(genre_name=DEFAULT_GENRE):
    """Constructs a Datastore key for a Genre entity.

    We use genre_name as the key.
    """
    return ndb.Key('Genre', genre_name.lower())

def cart_key(user):
    return ndb.Key('User', user)

#class Author(ndb.Model):
#    """Sub model for representing an author."""
#    identity = ndb.StringProperty(indexed=False)
#    email = ndb.StringProperty(indexed=False)


class Book(ndb.Model):
    """A main model for representing an individual Guestbook entry."""
    id = ndb.StringProperty(indexed=True)  # uniquely defines a book
    author = ndb.StringProperty(indexed=True)
    title = ndb.StringProperty(indexed=False)
    price = ndb.FloatProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)

class Cart(ndb.Model):
#     user = ndb.StringProperty(indexed=True)
    book_id = ndb.StringProperty()
    book_genre = ndb.StringProperty()
    
class MainPage(webapp2.RequestHandler):

    def get(self): 

        cookie_id = self.request.cookies.get('key')
        if cookie_id == None:
            cookie_id = random.randint(1000000000, 9999999999)
        
        user = users.get_current_user()
        if user:
            url = users.create_logout_url('/')
            nickname = user.nickname()
            hasLogin = True
        else:
            url = users.create_login_url('/')
            nickname = ''
            hasLogin = False                       
        
        genre_name = self.request.get('genre_name',
                                          DEFAULT_GENRE)
        genre_query = Book.query(
            ancestor=genre_key(genre_name.lower())).order(-Book.date)
        genre = genre_query.fetch(100)

#        user = users.get_current_user()
#        if user:
#            url = users.create_logout_url(self.request.uri)
#            url_linktext = 'Logout'
#        else:
#            url = users.create_login_url(self.request.uri)
#            url_linktext = 'Login'

        template_values = {
#           'user': user,
            'genre': genre,
            'genre_name': urllib.quote_plus(genre_name),
            'url': url,
            'nickname': nickname,
            'hasLogin': hasLogin,
#           'url': url,
#           'url_linktext': url_linktext,
        }

        print 'cookie_id', cookie_id
        print 'user', user

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))
        self.response.headers.add_header('Set-Cookie', 'key=%s' % str(cookie_id))        

class EnterPage(webapp2.RequestHandler):
    def get(self):
        genre_name = self.request.get('genre_name', DEFAULT_GENRE)
        error = self.request.get('error', DEFAULT_ERROR)
#        genre_query = Book.query(
#            ancestor=genre_key(genre_name.lower())).order(-Book.date)
#        genre = genre_query.fetch(100)
        template_values = {
#           'user': user,
#            'genre': genre,
            'genre_name': urllib.quote_plus(genre_name),
            'error': urllib.quote_plus(error),
#           'url': url,
#           'url_linktext': url_linktext,
        }

        template = JINJA_ENVIRONMENT.get_template('enter.html')
        self.response.write(template.render(template_values))

class Enter(webapp2.RequestHandler):
    def post(self):
        # We set the same parent key on the 'Greeting' to ensure each
        # Greeting is in the same entity group. Queries across the
        # single entity group will be consistent. However, the write
        # rate to a single entity group should be limited to
        # ~1/second.
        genre_name = self.request.get('genre_name',
                                          DEFAULT_GENRE)
        book = Book(parent=genre_key(genre_name.lower()))

#        if users.get_current_user():
#            greeting.author = Author(
#                    identity=users.get_current_user().user_id(),
#                    email=users.get_current_user().email())

        book.author = self.request.get('author')
        book.title = self.request.get('title')
        query_param1 = {'genre_name': genre_name}
        
#         genre_query = Book.query(ancestor=genre_key(
#                 genre_name.lower())).order(-Book.date).fetch(1)
#         if genre_query:
#             isbn = genre_query[0].isbn + 1
#         else:
#             isbn = 0
#         book.isbn = isbn
        
        def generateId():
            CHAR = [chr(i) for i in xrange(ord('A'), ord('Z')+1)] \
                    + [chr(i) for i in xrange(ord('a'), ord('z')+1)] \
                    + [chr(i) for i in xrange(ord('0'), ord('9')+1)]
            cart_id = ''
            for i in xrange(20):
                cart_id += CHAR[random.randint(0, len(CHAR) - 1)]
            return cart_id
        
        book.id = generateId()        
        
        is_float = True
        try:
            book.price = float(self.request.get('price'))        
        except:
            is_float = False

        if book.author != '' and book.title != '' and is_float:
            book.put()
            self.redirect('/?' + urllib.urlencode(query_param1))
        else:
            query_param2 = {'error': 'true'}
            self.redirect('/enter?' + urllib.urlencode(query_param1) + '&' + urllib.urlencode(query_param2))

class DisplayPage(webapp2.RequestHandler):
    def get(self):
        genre_name = self.request.get('genre_name', DEFAULT_GENRE)
        genre_query = Book.query(
            ancestor=genre_key(genre_name.lower())).order(-Book.date)
        genre = genre_query.fetch(100)
#        uncomment the following 2 lines to clear current entries in a genre
#        for book in genre:
#           book.key.delete()
        template_values = {
#           'user': user,
            'genre': genre,
            'genre_name': urllib.quote_plus(genre_name),
#           'url': url,
#           'url_linktext': url_linktext,
        }

        template = JINJA_ENVIRONMENT.get_template('display.html')
        self.response.write(template.render(template_values))

class Search(webapp2.RequestHandler):

    def get(self):
        genre_name = self.request.get('genre_name', DEFAULT_GENRE)
        author = self.request.get('author', DEFAULT_AUTHOR)
        author = author.lower()
        bookList = []
        genre_query = Book.query(
            ancestor=genre_key(genre_name.lower())).order(-Book.date)
        genre = genre_query.fetch(1000)
        if author != '':
            for book in genre:
                bookAuthor = book.author.lower()
                if bookAuthor.find(author) != -1:
                    bookList.append(book)
        
        template_values = {
#           'user': user,
            'bookList': bookList,
            'genre_name': urllib.quote_plus(genre_name),
            'author': urllib.quote_plus(author),
#           'url': url,
#           'url_linktext': url_linktext,
        }

        template = JINJA_ENVIRONMENT.get_template('search.html')
        self.response.write(template.render(template_values))

    def post(self):
        genre_name = self.request.get('genre_name', DEFAULT_GENRE)
        author = self.request.get('author')
        query_param1 = {'genre_name': genre_name}
        query_param2 = {'author': author}
        self.redirect('/search?' + urllib.urlencode(query_param1) + '&' + urllib.urlencode(query_param2))

class AddToCart(webapp2.RequestHandler):
    
    def post(self):
        user = users.get_current_user()
        if not user:
            user = self.request.cookies.get('key')
        else:
            user = user.email()
        books = self.request.get('book', allow_multiple=True)
        for book in books:
            cart = Cart(parent=cart_key(user))
            tokens = book.split('##')
            book_id, book_genre = tokens[0], tokens[1]
            cart.book_id = book_id
            cart.book_genre = book_genre
            cart.put()
        self.redirect('/cart?' + urllib.urlencode({'user': user}))

class DisplayCart(webapp2.RequestHandler):
    
    def get(self):
        user = users.get_current_user()
        if not user:
            user = self.request.cookies.get('key')
        else:
            user = user.email()
        cart = Cart.query(ancestor=cart_key(user))    
        
        total = 0
        books = []
        for item in cart:
            book = Book.query(ancestor=genre_key(item.book_genre.lower())).filter(Book.id == item.book_id).fetch(1)            
            total += book[0].price
            books.extend(book)
        
        template_values = {
            'cart': books,
            'total': total,
        }

        template = JINJA_ENVIRONMENT.get_template('cart.html')
        self.response.write(template.render(template_values))                

class Checkout(webapp2.RequestHandler):
    
    def get(self):
        pass
    
    def post(self):
        user = users.get_current_user()
        if not user:
            url = users.create_login_url('/checkout')
            self.redirect(url)
        else:
            user = user.email()
        

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/enter', EnterPage),
    ('/add', Enter),
    ('/display', DisplayPage),
    ('/search', Search),
    ('/add-to-cart', AddToCart),
    ('/cart', DisplayCart),
    ('/checkout', Checkout),
], debug=False)
