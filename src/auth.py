from flask import Blueprint, flash, render_template, redirect, url_for, request, jsonify, session
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import uuid
from .models import Producer, Consumer, Login, Product, Cart, CartItem
from . import db
import os

auth_routes = Blueprint("auth", __name__)
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

login_manager.login_message_category = "error"

def initialize_login(app):
    login_manager.init_app(app)

ID_PDF_UPLOAD_FOLDER = os.path.join(os.getcwd(), 'upload_id_card')

os.makedirs(ID_PDF_UPLOAD_FOLDER, exist_ok=True)

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@login_manager.user_loader
def load_user(id):
    return Login.query.get(int(id))

def print_database():
    # Query all records from each table
    producers = Producer.query.all()
    consumers = Consumer.query.all()
    logins = Login.query.all()
    products = Product.query.all()
    cart = Cart.query.all()
    cartitems = CartItem.query.all()


    # Print to the terminal
    print("\n--- Producers ---")
    for producer in producers:
        print(f"ID: {producer.id}, Name: {producer.name}, Email: {producer.email}, Producer ID: {producer.producer_id}")
    
    print("\n--- Consumers ---")
    for consumer in consumers:
        print(f"ID: {consumer.id}, Name: {consumer.name}, Consumer ID: {consumer.consumer_id}")

    print("\n--- Products ---")
    for product in products:
        print(f"ID: {product.id}, Name: {product.title}, Producer ID: {product.producer_id}, Description : {product.description}")


    print("\n--- Logins ---")
    for login in logins:
        print(f"id:{login.id}, pass: {login.password} User ID: {login.user_id}, User Type: {login.user_type}")

    print("\n--- Cart ---")
    for c in cart:
        print(f"id:{c.id}, pass: {c.consumer_id}, User Type: {c.cart_items}")

    print("\n--- cart item ---")
    for cartitem in cartitems:
        print(f"id:{cartitem.id}, cart_id: {cartitem.cart_id}, product_id: {cartitem.product_id}, product title: {products[cartitem.product_id].title}, cartitem quantity: {cartitem.quantity}")



@auth_routes.route("/login", methods=["GET", "POST"])
def login():
    print_database()
    if request.method == "POST":
        user_id = request.form.get("user_id")
        password = request.form.get("password")

        user = Login.query.filter_by(user_id=user_id).first()

        if user and password:
            if check_password_hash(user.password, password):
                login_user(user, remember=True)
                flash("Logged in successfully", "success")
                if user.user_type == 'producer':
                    return redirect(url_for("views.product"), code=302)
                elif user.user_type == 'consumer':
                    return redirect(url_for("views.product"), code=302)
            else:
                flash("Incorrect password", "error")
        else:
            flash("You need to sign up first", "error")

    return render_template("login2.html")


@auth_routes.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


ALLOWED_EXTENSIONS = {'pdf'}

# Make sure the upload folder exists
@auth_routes.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name")      
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")
        userrole = request.form.get("userrole")        

        if userrole == "producer":
            email = request.form.get("email")
            producer_id = request.form.get("producer_id")
            # Check if email already exists
            user = Producer.query.filter_by(email=email).first()
            if user:
                flash("Email already in use", "error")
                return redirect(url_for("auth.login"))

        elif userrole == "consumer":
            # specialization = request.form.get("specialization")
            consumer_id = request.form.get("consumer_id")

        # Validate passwords
        if password1 != password2:
            flash("Passwords do not match", "error")
        elif password1:            
            if userrole == "producer":
                # Create new producer user
                login_user = Login(user_id=producer_id, password=generate_password_hash(password1), user_type="producer")
                new_user = Producer(
                    name=name,
                    email=email,
                    password=generate_password_hash(password1),
                    producer_id=producer_id
                )

            elif userrole == "consumer":
                # Create new consumer user
                login_user = Login(user_id=consumer_id, password=generate_password_hash(password1), user_type="consumer")
                new_user = Consumer(name=name, consumer_id=consumer_id)
            
            # Add new login and user records
            db.session.add(login_user)
            db.session.commit()

            db.session.add(new_user)
            db.session.commit()
            flash(f"Welcome {name}, you have been successfully registered!", "success")
            return redirect(url_for("auth.login"))

        else:
            flash("Password cannot be empty", "error")

    return render_template("signup.html")
