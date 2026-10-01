from mpesa_utils import send_stk_push
import os
from flask import Flask, render_template, request, redirect, url_for
from models import db, Furniture, Order

# --- 1. CONFIGURATION ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'smartex_secret_key_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///smartex.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# --- 2. DATABASE INITIALIZATION ---
db.init_app(app)

with app.app_context():
    db.create_all()

# --- 3. ROUTES ---

@app.route('/')
def home():
    items = Furniture.query.all()
    return render_template('index.html', items=items)

@app.route('/admin/upload', methods=['GET', 'POST'])
def upload_stock():
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        stock = request.form.get('stock')
        desc = request.form.get('desc')
        image = request.files.get('image')

        if image:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
            image.save(image_path)
            new_furniture = Furniture(
                name=name, 
                price=float(price), 
                stock_level=int(stock), 
                description=desc, 
                image_file=image.filename
            )
            db.session.add(new_furniture)
            db.session.commit()
            return redirect(url_for('home'))
    return render_template('admin.html')

@app.route('/checkout/<int:item_id>', methods=['POST'])
def checkout(item_id):
    product = Furniture.query.get_or_404(item_id)
    phone = request.form.get('phone')
    
    # Trigger M-Pesa
    response = send_stk_push(phone, product.price)
    
    # This is the new "Memory" part you are adding
    new_order = Order(
        customer_phone=phone,
        product_name=product.name,
        amount=product.price,
        status='Pending',
        checkout_request_id=response.get('CheckoutRequestID')
    )
    db.session.add(new_order)
    db.session.commit()
    
    return f"<h1>Prompt Sent to 0{phone[-9:]}!</h1><p>Check your phone to complete payment.</p>"
@app.route('/orders')
def view_orders():
    # Fetch all orders, newest at the top
    all_orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('orders.html', orders=all_orders)

@app.route('/callback', methods=['POST'])
def mpesa_callback():
    data = request.get_json()
    # Ensure the lines below are indented exactly 4 spaces
    stk_callback = data['Body']['stkCallback']
    result_code = stk_callback['ResultCode']
    merchant_id = stk_callback['MerchantRequestID']
    
    if result_code == 0:
        order = Order.query.filter_by(checkout_request_id=merchant_id).first()
        if order:
            order.status = 'Paid'
            db.session.commit()
            print("💰 PAYMENT SUCCESSFUL!")
            
    return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

