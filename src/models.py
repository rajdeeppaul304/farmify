from . import db
from flask_login import UserMixin
from datetime import datetime
import base64
import os

# PROPOSAL_FOLDER = os.path.join(os.getcwd(), 'proposals')

# producer
class Producer(db.Model):
    __tablename__ = 'producer'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True) 
    name = db.Column(db.String(300))
    email = db.Column(db.String(300), unique=True)
    password = db.Column(db.String(200))
    producer_id = db.Column(db.String, unique=True)

    def __init__(self, name, email, password, producer_id):
        self.name = name
        self.email = email
        self.password = password
        self.producer_id = producer_id

# consumer
class Consumer(db.Model):
    __tablename__ = 'consumer'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  
    name = db.Column(db.String(300))
    consumer_id = db.Column(db.String, unique=True)

    # Relationship to Cart
    cart = db.relationship('Cart', backref='consumer', uselist=False)

    def __init__(self, name, consumer_id):
        self.name = name
        self.consumer_id = consumer_id

# products
class Product(db.Model):
    __tablename__ = 'product'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.String, unique=True)

    producer_id = db.Column(db.Integer, db.ForeignKey('producer.id'))
    title = db.Column(db.String(300))
    description = db.Column(db.String(1000))
    price = db.Column(db.Float)  # Added price column (as a floating point number)
    image = db.Column(db.Text)   # Added image column (base64 encoded string)

    # Relationship to Producer
    producer = db.relationship('Producer', backref='products', lazy='joined')

    def __init__(self, product_id, producer_id, title, description, price, image=None):
        self.product_id = product_id
        self.producer_id = producer_id
        self.title = title
        self.description = description
        self.price = price
        self.image = image  # If you want to set an image, you can provide the base64 string



class Login(db.Model, UserMixin):
    __tablename__ = 'login'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  
    user_id = db.Column(db.String, unique=True)  # FK reference can be added if needed
    password = db.Column(db.String(200))
    user_type = db.Column(db.String(50))  # To distinguish between Farmer and Consumer.
    
    def __init__(self, user_id, password, user_type):
        self.user_id = user_id
        self.password = password
        self.user_type = user_type

# Cart
class Cart(db.Model):
    __tablename__ = 'cart'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    consumer_id = db.Column(db.Integer, db.ForeignKey('consumer.id'), nullable=False)

    # Relationship to CartItem
    cart_items = db.relationship('CartItem', backref='cart', lazy=True)

    def __init__(self, consumer_id):
        self.consumer_id = consumer_id

# CartItem
class CartItem(db.Model):
    __tablename__ = 'cart_item'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    # Relationship to Product
    product = db.relationship('Product', backref='cart_items', lazy=True)

    def __init__(self, cart_id, product_id, quantity):
        self.cart_id = cart_id
        self.product_id = product_id
        self.quantity = quantity
