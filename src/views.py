from flask import Blueprint, flash, render_template, redirect, url_for, request, jsonify, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy.orm import joinedload

from .models import Producer, Consumer, Product

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
    
    # Fetch all products submitted by the producer, along with the associated consumer details
    products = Product.query.filter_by(producer_id=producer.id).all()


    # Serialize products to a list of dictionaries
    products_dict = [{
        'id': product.id,
        'title': product.title,
        'description': product.description,
    } for product in products]
    
    # Pass the serialized products to the template
    return render_template("product.html", products=products, products_dict=products_dict, current_page='index', producer=producer)


@view_routes.route("/submit_product", methods=['GET', 'POST'])
@login_required
def submit_product():
    if request.method == 'POST':
        # Get form data
        # consumer_id = request.form['consumer']  # Consumer ID, not name
        title = request.form['title']
        description = request.form['description']
        # file = request.files['file']
        producer = Producer.query.filter_by(producer_id=current_user.user_id).first()

        product_id = f"{current_user.user_id}_{uuid.uuid4()}"

        # Create and save the product object to the database
        new_product = Product(
            product_id=product_id,
            producer_id=producer.id,
            title=title,
            description=description,
        )
        db.session.add(new_product)
        db.session.commit()

        return redirect(url_for('views.product'))
    
    # Fetch all consumers to populate the dropdown
    producer = Producer.query.filter_by(producer_id=current_user.user_id).first()
    products = Product.query.filter_by(producer_id=producer.id).all()


    print(producer, products)
    # Query the Slot table to get consumers who have slots
    # slots = db.session.query(Slot).filter(Slot.consumer_id != None).all()
    
    consumer_data = {}

    # for slot in slots:
    #     consumer = Consumer.query.filter_by(id = slot.consumer_id).first()
    #     consumer_data[consumer.id] = {
    #         'name': consumer.name,
    #         'slot_count': slot.slot_count,
    #         'slot_filled': slot.slot_filled
    #     }
    
    return render_template("submit_product.html", consumer_data=consumer_data, producer=producer, current_page='submit_product')


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
