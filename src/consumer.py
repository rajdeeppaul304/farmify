import uuid
from flask import Blueprint, flash, render_template, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from .models import Producer, Consumer, Product, Cart, CartItem
from . import db
from datetime import datetime

consumer_routes = Blueprint("consumer", __name__)


@consumer_routes.route("/", methods=["GET", "POST"])
@login_required
def consumer_index():
    if current_user.user_type != 'consumer':
        flash("You do not have access to this page", "error")
        return redirect(url_for("views.index"))

    consumer = Consumer.query.filter_by(consumer_id=current_user.user_id).first()

    if not consumer:
        flash("Consumer not found.", "error")
        return redirect(url_for("views.index"))

    # Fetch all products
    products = Product.query.all()

    producers = Producer.query.all()

    # Serialize products to include price, image, and producer name
    products_dict = [{
        'id': product.id,
        'title': product.title,
        'description': product.description,
        'price': product.price,  # Add price
        'image': product.image,  # Add image (Base64)
        'producer': producers[product.producer_id - 1].name
    } for product in products]

    return render_template("consumer/product.html", products=products, products_dict=products_dict)







@consumer_routes.route("/add_to_cart/<int:product_id>", methods=["POST"])
@login_required
def add_to_cart(product_id):
    if current_user.user_type != 'consumer':
        flash("You do not have access to this page", "error")
        return redirect(url_for("views.index"))

    # Get the consumer object based on the logged-in user
    consumer = Consumer.query.filter_by(consumer_id=current_user.user_id).first()
    
    if not consumer:
        flash("Consumer not found.", "error")
        return redirect(url_for("views.index"))

    # Fetch the product to add to the cart
    product = Product.query.get(product_id)
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("consumer.consumer_index"))
    

    quantity_added = int(request.form['quantity'])
    print(product_id, quantity_added)

    if quantity_added<0:
        flash("quantity is not correct.", "error")
        return redirect(url_for("consumer.consumer_index"))


    
    # Check if the consumer already has a cart
    cart = Cart.query.filter_by(consumer_id=consumer.id).first()
    if not cart:
        # If no cart exists, create one
        cart = Cart(consumer_id=consumer.id)
        db.session.add(cart)
        db.session.commit()

    # Check if the product is already in the cart
    cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product.id).first()

    if cart_item:
        # If the product is already in the cart, update the quantity
        cart_item.quantity = quantity_added
        if cart_item.quantity == 0:
            db.session.delete(cart_item)
            
    else:
        # If the product is not in the cart, create a new cart item
        cart_item = CartItem(cart_id=cart.id, product_id=product.id, quantity=quantity_added)
        db.session.add(cart_item)

    db.session.commit()
    flash(f"{product.title} has been added to your cart.", "success")
    return redirect(url_for("consumer.consumer_index"))




@consumer_routes.route("/cart_items", methods=["GET"])
@login_required
def get_cart_items():
    if current_user.user_type != 'consumer':
        return jsonify({"error": "Access denied"}), 403

    # Get the consumer object
    consumer = Consumer.query.filter_by(consumer_id=current_user.user_id).first()
    
    if not consumer:
        return jsonify({"error": "Consumer not found"}), 404

    # Fetch the cart and its items
    cart = Cart.query.filter_by(consumer_id=consumer.id).first()
    if not cart:
        return jsonify({"message": "No items in the cart"}), 200

    cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
    items = [{
        "product_id": item.product.id,
        "title": item.product.title,
        "description": item.product.description,
        "quantity": item.quantity,
        "price": item.product.price,  # Add product price to the response
        "image": item.product.image   # Add product image (base64 string) to the response
    } for item in cart_items]

    return jsonify(items)  # Return the cart items as JSON
