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

DEFAULT_GENRE  = 'Non-fiction'
DEFAULT_AUTHOR = 'zzzzzzzzzzz'
DEFAULT_ERROR  = 'false'

def genre_key(genre_name=DEFAULT_GENRE):
    """Constructs a Datastore key for a Genre entity. We use genre_name as the key."""
    return ndb.Key('Genre', genre_name.lower())

def cart_key(user):
    return ndb.Key('User', user)

class Book(ndb.Model):
    """A main model for representing an individual Book entry."""
    id = ndb.StringProperty(indexed=True)  # uniquely defines a book
    author = ndb.StringProperty(indexed=True)
    title = ndb.StringProperty(indexed=False)
    price = ndb.FloatProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)

class Cart(ndb.Model):
    book_id = ndb.StringProperty()  # Does not store the entire book in the cart; only the id and genre
    book_genre = ndb.StringProperty()
    
class MainPage(webapp2.RequestHandler):

    def get(self): 

        cookie_id = self.request.cookies.get('key')  # if first time, then generate an cookie_id
        if cookie_id == None:
            cookie_id = str(random.randint(1000000000, 9999999999))
        
        user = users.get_current_user()  # display different login info depending on whether the user has logged in
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

        template_values = {
            'genre': genre,
            'genre_name': urllib.quote_plus(genre_name),
            'url': url,
            'nickname': nickname,
            'hasLogin': hasLogin,
        }

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))
        self.response.headers.add_header('Set-Cookie', 'key=%s' % str(cookie_id))        

class EnterPage(webapp2.RequestHandler):
    def get(self):
        genre_name = self.request.get('genre_name', DEFAULT_GENRE)
        error = self.request.get('error', DEFAULT_ERROR)
        
        template_values = {
            'genre_name': urllib.quote_plus(genre_name),
            'error': urllib.quote_plus(error),
        }

        template = JINJA_ENVIRONMENT.get_template('enter.html')
        self.response.write(template.render(template_values))

class Enter(webapp2.RequestHandler):
    def post(self):
        genre_name = self.request.get('genre_name',
                                          DEFAULT_GENRE)
        book = Book(parent=genre_key(genre_name.lower()))

        book.author = self.request.get('author')
        book.title = self.request.get('title')
        query_param1 = {'genre_name': genre_name}
        
        def generateId():  # generate an unique id for each book, so that in the shopping cart we only need to store the id
            CHAR = [chr(i) for i in xrange(ord('A'), ord('Z')+1)] \
                    + [chr(i) for i in xrange(ord('a'), ord('z')+1)] \
                    + [chr(i) for i in xrange(ord('0'), ord('9')+1)]
            book_id = ''
            for i in xrange(20):
                book_id += CHAR[random.randint(0, len(CHAR) - 1)]
            return book_id
        
        book.id = generateId()        
        
        is_float = True  # check the validity of the price
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
        
        template_values = {
            'genre': genre,
            'genre_name': urllib.quote_plus(genre_name),
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
            'bookList': bookList,
            'genre_name': urllib.quote_plus(genre_name),
            'author': urllib.quote_plus(author),
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
        books = self.request.get('book', allow_multiple=True)  # get all the books that has been marked in the check box
        for book in books:
            cart = Cart(parent=cart_key(user))
            tokens = book.split('##')
            book_id, book_genre = tokens[0], tokens[1]
            cart.book_id = book_id  # only store the book id and genre in the cart database
            cart.book_genre = book_genre
            cart.put()
        self.redirect('/cart?' + urllib.urlencode({'user': user}))

class DisplayCart(webapp2.RequestHandler):
    
    def get(self):
        user = users.get_current_user()
        user_name = 'false'
        if not user:
            user = self.request.cookies.get('key')
        else:
            user = user.email()
            user_name = user
            cookie_id = self.request.cookies.get('key')
            cart_temp = Cart.query(ancestor=cart_key(cookie_id))
            if cart_temp:  # if the user has logged in, then merge the temporary cart with his/her cart
                for book in cart_temp:
                    cart = Cart(parent=cart_key(user))
                    cart.book_id = book.book_id
                    cart.book_genre = book.book_genre
                    cart.put()
                    book.key.delete() 
        cart = Cart.query(ancestor=cart_key(user))    
        
        total = 0
        books = []
        for item in cart:  # count the total price
            book = Book.query(ancestor=genre_key(item.book_genre.lower())).filter(Book.id == item.book_id).fetch(1)            
            total += book[0].price
            books.extend(book)
        
        template_values = {
            'cart': books,
            'total': total,
            'checkout': self.request.get('checkout'),
            'user_name': user_name,
        }

        template = JINJA_ENVIRONMENT.get_template('cart.html')
        self.response.write(template.render(template_values))                

class CartOperations(webapp2.RequestHandler):
    
    def post(self):
        
        button_checkout = self.request.get("checkout")  # check which button in the <form> has been clicked
        button_remove = self.request.get("remove")
        
        if button_checkout:  # the checkout button has been clicked
            user = users.get_current_user()
            if user == None:
                url = users.create_login_url('/cart')
                self.redirect(url)              
            else:
                user = user.email()       
                cart_temp = Cart.query(ancestor=cart_key(user))
                for book in cart_temp:
                    book.key.delete()
                self.redirect('/cart?' + urllib.urlencode({'user': user}) + '&' + urllib.urlencode({'checkout': 'true'}))
        
        if button_remove:  # the remove button has been clicked on
            book_id = button_remove  # the value of the button is the book id
            user = users.get_current_user()
            if not user:
                user = self.request.cookies.get('key')
            else:
                user = user.email()
            cart = Cart.query(ancestor=cart_key(user))
            for book in cart:
                if book.book_id == book_id:  # delete the book only once
                    book.key.delete()
                    break
            self.redirect('/cart?' + urllib.urlencode({'user': user}))
        

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/enter', EnterPage),
    ('/add', Enter),
    ('/display', DisplayPage),
    ('/search', Search),
    ('/add-to-cart', AddToCart),
    ('/cart', DisplayCart),
    ('/cart-operations', CartOperations),
], debug=False)
