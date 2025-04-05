from flask import Blueprint, flash, render_template, redirect, url_for, request, jsonify, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy.orm import joinedload
import base64

from .models import Producer, Consumer, Product, CartItem, Cart

from . import db

import os
import uuid
view_routes = Blueprint("views", __name__)

PRODUCT_FOLDER = os.path.join(os.getcwd(), 'products')

# Create the directory if it doesn't exist
if not os.path.exists(PRODUCT_FOLDER):
    os.makedirs(PRODUCT_FOLDER)


@view_routes.route("/")
def index():
    # If current user is a consumer, redirect them to the consumer dashboard (this is just an example)
    # if current_user.user_type == 'consumer':
    #     return redirect(url_for("consumer.consumer_index"))
    
    return render_template("index.html", current_page='index')


@view_routes.route('/product/<filename>')
def serve_product(filename):
    # Ensure the file exists in the products directory
    return send_from_directory(PRODUCT_FOLDER, filename)


@view_routes.route("/product", methods=['GET'])
@login_required
def product():
    if current_user.user_type == 'consumer':
        return redirect(url_for("consumer.consumer_index"))
    
    # Get the producer object from the database based on the current logged-in user
    producer = Producer.query.filter_by(producer_id=current_user.user_id).first()
    
    if not producer:
        flash("Producer not found.", "error")
        return redirect(url_for('producer.dashboard'))
    
    # Fetch all products submitted by the producer
    products = Product.query.filter_by(producer_id=producer.id).all()

    # Serialize products to a list of dictionaries
    products_dict = [{
        'id': product.id,
        'title': product.title,
        'description': product.description,
        'price': product.price,  # Add price to the dictionary
        'image': product.image   # Add image (base64 string) to the dictionary
    } for product in products]
    
    # Pass the serialized products to the template
    return render_template("product.html", products=products, products_dict=products_dict, current_page='index', producer=producer)


@view_routes.route("/delete_product/<int:product_id>", methods=['POST'])
@login_required
def delete_product(product_id):
    if current_user.user_type == 'consumer':
        return redirect(url_for("consumer.consumer_index"))
    
    # Get the producer object based on the logged-in user
    producer = Producer.query.filter_by(producer_id=current_user.user_id).first()
    
    if not producer:
        flash("Producer not found.", "error")
        return redirect(url_for('producer.dashboard'))
    
    # Find the product to be deleted
    product = Product.query.get(product_id)
    if not product or product.producer_id != producer.id:
        flash("Product not found or you do not have permission to delete this product.", "error")
        return redirect(url_for("views.product"))
    
    # Step 1: Find all CartItems with the product_id
    cart_items_to_delete = CartItem.query.filter_by(product_id=product_id).all()

    # Step 2: Store cart_id and cart_item_id for deleted CartItems
    deleted_cart_items_info = []
    for cart_item in cart_items_to_delete:
        deleted_cart_items_info.append({'cart_id': cart_item.cart_id, 'cart_item_id': cart_item.id})
        db.session.delete(cart_item)

    # Step 3: Commit the deletion of CartItems
    db.session.commit()

    # Step 4: Now, for each cart, remove the empty CartItems that were deleted
    for deleted_info in deleted_cart_items_info:
        cart = Cart.query.get(deleted_info['cart_id'])
        if cart:
            # Remove the reference to the deleted CartItem in the cart
            cart_item_to_remove = CartItem.query.get(deleted_info['cart_item_id'])
            if cart_item_to_remove in cart.cart_items:
                cart.cart_items.remove(cart_item_to_remove)

    # Step 5: Finally, delete the product itself
    db.session.delete(product)
    db.session.commit()

    flash("Product and associated cart items deleted successfully.", "success")
    return redirect(url_for("views.product"))


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Function to check the file extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@view_routes.route("/submit_product", methods=['GET', 'POST'])
@login_required
def submit_product():
    if request.method == 'POST':
        # Get form data
        title = request.form['title']
        description = request.form['description']
        price = float(request.form['price'])  # Convert price to float

        # Process the image upload
        image = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                # Convert the image to base64 encoding
                image_data = file.read()
                image = base64.b64encode(image_data).decode('utf-8')

        # Get the producer based on the current user
        producer = Producer.query.filter_by(producer_id=current_user.user_id).first()

        # Create a unique product ID
        product_id = f"{current_user.user_id}_{uuid.uuid4()}"

        # Create and save the product object to the database
        new_product = Product(
            product_id=product_id,
            producer_id=producer.id,
            title=title,
            description=description,
            price=price,
            image=image  # Save the base64 image if it exists
        )
        db.session.add(new_product)
        db.session.commit()

        return redirect(url_for('views.product'))

    # Fetch the producer data to pass to the form
    producer = Producer.query.filter_by(producer_id=current_user.user_id).first()

    return render_template("submit_product.html", producer=producer, current_page='submit_product')


@view_routes.route("/withdraw_product/<product_id>", methods=['POST'])
@login_required
def withdraw_product(product_id):
    # Find the product by ID
    product = Product.query.filter_by(product_id=product_id).first()
    producer = Producer.query.filter_by(producer_id=current_user.user_id).first()

    if not product:
        flash("Product not found.", "error")
        return redirect(url_for('views.product'))

    # Make sure the current user is the one who submitted the product
    if product.producer_id != producer.id:
        flash("You can only withdraw your own products.", "error")
        return redirect(url_for('views.product'))
    
    # Change the status to 'Withdrawn'
    if product.status == "Pending":
        product.status = 'Withdrawn'
    db.session.commit()

    flash("Your product has been withdrawn.", "success")
    return redirect(url_for('views.product'))


@view_routes.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    # Get the current producer by producer_id
    producer = Producer.query.filter_by(producer_id=current_user.user_id).first()

    if not producer:
        flash("Producer not found.", "error")
        return redirect(url_for('producer.view_profile'))

    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        program = request.form.get('program')
        year = request.form.get('year')
        email = request.form.get('email')
        
        # Check if the email is unique
        existing_producer = Producer.query.filter_by(email=email).first()
        if existing_producer and existing_producer.id != producer.id:
            flash("This email is already registered with another account.", "error")
            return redirect(url_for('producer.edit_profile'))

        # Update producer details
        producer.name = name
        producer.program = program
        producer.year = year
        producer.email = email

        # Commit changes to the database
        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for('views.edit_profile'))

    return render_template('edit_profile.html', producer=producer, current_page='edit_profile')
