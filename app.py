from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2
from psycopg2 import IntegrityError
import base64
import random
import smtplib
import random
import bcrypt
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__, static_folder='static')
app.secret_key = '368a15bbaa36d4f87ae7d8739194b7c5'


mydata = psycopg2.connect('postgres://vcipmdui:0M4mNm6yaFpPEnoUflg6B3YgZNpK5hF8@kandula.db.elephantsql.com/vcipmdui')
cursor = mydata.cursor()

# ==========  Start Home  ==========
user_name = None
@app.route("/")
def index():
    global user_name
    return render_template('index.html', user_name=user_name)
# ==========  End Home  ==========

# ==========  Start Products  ==========
products = "SELECT * FROM products ORDER BY id"
cursor.execute(products)
result = cursor.fetchall()
data = result

@app.route("/products")
def products():
    global user_name, data  
    items_list = list(enumerate(data))
    return render_template('products.html', item=items_list, user_name=user_name)


@app.route("/product_items/<int:item_index>")
def product_items(item_index):
    selected_item = data[item_index]
    print(selected_item[::3])
    products = list(enumerate(data))
    start_index = item_index + 1
    if start_index == len(data):
        modified_item = [(item_index, selected_item)]
    else:
        modified_item = products[start_index:start_index + 5]

    return render_template("items.html", selected_item=selected_item, item=modified_item)
# ==========  End Products  ==========

# ==========  Sart Cart  ==========
cart = []
@app.route("/cart")
def view_cart():
    global user_name, cart, wishlist
    enumerated_list = list(enumerate(cart))
    item_price = 0
    for item in cart:
        item_price += float(item['price'])
    return render_template('cart.html', cart=enumerated_list, user_name=user_name, item_price=int(item_price))

@app.route("/add_to_cart/<int:item_index>")
def add_to_cart(item_index):
    global data, cart, user_name
    selected_item = data[item_index]
    item_id = selected_item[0]

    if user_name is None:
        flash("You need to log in first")
        return redirect (url_for('login'))
    else:
        if item_id not in [item['id'] for item in cart]:
            cart.append({'id':selected_item[0],
                        'name':selected_item[1],
                        'price':selected_item[2],
                        'rating':selected_item[3],
                        'description':selected_item[4],
                        'image':selected_item[5]})
            flash("item successfully add to your cart")
        else:
            flash("Item is already in your cart")

    return redirect(url_for("product_items",item_index=selected_item))

@app.route("/remove_from_cart/<int:item_index>")
def remove_from_cart(item_index):
    global cart
    cart.pop(item_index)
    return redirect('/cart')

@app.route("/move_to_wishlist/<int:item_index>")
def move_to_wishlist(item_index):
    global cart, wishlist
    selected_item = cart[item_index]
    if selected_item not in wishlist:
        wishlist.append(selected_item)
    cart.pop(item_index)
    return redirect('/cart')
# ==========  End Cart  ==========

# ==========  Start Wishlist  ==========
wishlist = []
@app.route("/wishlist")
def view_wishlist():
    global wishlist, user_name, cart
    enumerated_list = list(enumerate(wishlist))
    return render_template('wishlist.html', wishlist=enumerated_list, user_name=user_name)

@app.route("/add_to_wishlist/<int:item_index>")
def add_to_wishlist(item_index):
    global data, wishlist, user_name
    selected_item = data[item_index]
    item_id = selected_item[0]

    if user_name is None:
        flash("You need to log-in first")
        return redirect (url_for('login'))
    else:
        if item_id not in [item['id'] for item in wishlist]:
            wishlist.append({'id':selected_item[0],
                        'name':selected_item[1],
                        'price':selected_item[2],
                        'rating':selected_item[3],
                        'description':selected_item[4],
                        'image':selected_item[5]})
            flash("item successfully add to your wishlist")
        else:
            flash("item already in your wishlist")
    return redirect('/products')

@app.route("/remove_from_wishlist/<int:item_index>")  
def remove_from_wishlist(item_index):
    global wishlist
    wishlist.pop(item_index)
    return redirect('/wishlist')

@app.route("/move_to_cart/<int:item_index>")
def move_to_cart(item_index):
    global cart, wishlist
    selected_item = wishlist[item_index]
    if selected_item not in cart:
        cart.append(selected_item)
    wishlist.pop(item_index)
    return redirect('/wishlist')
# ==========  End Wishlist  ==========

# ==========  start Order  ==========
order_count = 0
products_ordered = 0

@app.route("/order")
def order():
    global cart, order_count, products_ordered
    if cart:
        order_count += 1
        for product in cart:
            products_ordered += 1
        cart.clear()
        flash("Order placed successfully! Thank you for shopping.")
        return redirect(url_for("view_cart"))
    else:
        flash("Your cart is empty. Please add items to your cart before placing an order.")
        return redirect(url_for("view_cart"))
# ==========  End Order  ==========

# ==========  start Login  ==========
@app.route("/login")
def login():
    global user_name
    return render_template("login/login.html", user_name=user_name)

@app.route("/login_verify", methods=['POST'])
def login_verify():
    global user_name
    if request.method == 'POST':
        user_email = request.form.get('email')
        user_password = request.form.get('password')
        database_query = "SELECT email, password, first_name FROM user_details WHERE email = %s"
        admin_email = 'admin@gmail.com'
        admin_password = 'admin@123'

        try:
            cursor.execute(database_query, (user_email,))
            result = cursor.fetchone()

            if user_email == admin_email and bcrypt.checkpw(user_password.encode('utf-8'), bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())):
                user_name = "admin"
                flash("Admin login successful")
                return redirect(url_for('home'))
            elif user_email == admin_email and not bcrypt.checkpw(user_password.encode('utf-8'), bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())):
                flash("Admin password is incorrect: Try again")
                return redirect(url_for('login'))
            elif result:
                stored_hashed_password_hex = result[1]
                user_entered_password = user_password
                stored_hashed_password_bytes = bytes.fromhex(stored_hashed_password_hex[2:])  # Remove leading \x
                hashed_user_entered_password = bcrypt.hashpw(user_entered_password.encode('utf-8'), stored_hashed_password_bytes)
                if hashed_user_entered_password == stored_hashed_password_bytes:
                    user_name = result[2]
                    flash("User login successful")
                    return redirect(url_for('index'))
                else:
                    flash("Incorrect password. Please try again.")
            else:
                flash("User not found. If you don't have an account, please create one.")
        except IntegrityError as e:
            flash(f"An error occurred: {e}. Please try again.")
 
    return redirect(url_for('login'))

@app.route("/logout")
def logout():
    global user_name
    user_name = None
    return render_template("login/login.html", user_name=user_name)
# ==========  End Login  ==========

# ==========  Start Forgot_Password  ==========
generate_code = 0
user_email = ""
def generate_verification_code():
    global generate_code
    code = random.randint(1000, 9999)
    generate_code = code
    return code

def send_verification_email(receiver_email, verification_code):
    sender_email = "deshwaltushar17@gmail.com"
    sender_password = "fbjh yimw lywg bbsh"
    subject = "Email Verification Code"

    # Email content
    body = f"Your verification code is: {verification_code}"

    # Create message
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    # Connect to SMTP server and send email
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, message.as_string())

@app.route("/forgot")
def forgot():
    return render_template("login/send_code.html")

@app.route("/send_code", methods=["POST"])
def send_code():
    global user_email
    if request.method == "POST":
        
        receiver_email = request.form.get('email')
        verification_code = generate_verification_code()
        
        user_email = receiver_email

        send_verification_email(receiver_email, verification_code)
        flash("Code has been sent to your email. Please check.")
    
    return render_template("login/verify_code.html")

@app.route("/verify_code", methods=["POST"])
def verify_code():
    global generate_code
    if request.method == "POST":
        user_code = request.form.get('code')

        if generate_code:
            stored_code = generate_code
            if user_code == str(stored_code):
                flash("Verification successful!")
                generate_code = 0
                return render_template("login/set_password.html")
            else:
                flash("Your code is incorrect. Verification failed.")
        else:
            flash("Verification code not found. Please request a new one.")

    return redirect(url_for("forgot"))

@app.route("/set_password", methods=["POST"])
def set_password():
    global user_email
    if request.method == "POST":
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")
        user_emails = user_email

        if new_password != confirm_password:
            flash("Your password is not match: Try again!")

        criteria = verify_password(new_password)

        if criteria:
            for message in result:
                flash(message)
        else:
            # Hash the new password
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

            # Update the password in the database
            update_query = "UPDATE user_details SET password = %s WHERE email = %s"
            values = (hashed_password, user_emails)

            try:
                cursor.execute(update_query, values)
                mydata.commit()
                flash("Your password has been updated successfully.")
                return redirect(url_for("login"))
            except Exception as e:
                flash(f"Error updating password: {str(e)}")
                return redirect(url_for("login"))

    return render_template("set_password.html")
# ==========  End Forgot_Password  ==========

# ==========  Start Sign-Up  ==========
@app.route("/signup")
def signup():
    return render_template("login/signup.html")

@app.route("/add_user", methods=['POST'])
def add_user():
    global count_users
    if request.method == 'POST':
        user_id = count_users + 1
        user_first_name = request.form['name']
        user_last_name = request.form['last']
        user_email = request.form['email']
        user_email_password = request.form['password']
        user_phone_number = request.form['number']

        criteria = verify_password(user_email_password)

        if criteria:
            for message in result:
                flash(message)
        else:
            if len(user_email_password) < 8:
                flash("Password must be at least 8 characters long.")
            else:
                hashed_password = bcrypt.hashpw(user_email_password.encode('utf-8'), bcrypt.gensalt())

                query = "INSERT INTO user_details (id, first_name, last_name, number, email, password) VALUES (%s, %s, %s, %s, %s, %s)"
                values = (user_id, user_first_name, user_last_name, user_phone_number, user_email, hashed_password)

                try:
                    cursor.execute(query, values)
                    mydata.commit()
                    flash("User added successfully")
                    return redirect(url_for("login"))
                except Exception as e:
                    flash(f"Error adding user: {str(e)}")
    return redirect(url_for("signup"))

# ==========  End Sign-Up  ==========

# ==========  Verify User Deatils Criteria  ==========
def verify_password(password):
    messages = []

    if len(password) < 8:
        messages.append("Password must be at least 8 characters long.")

    if not re.search(r"[A-Z]", password):
        messages.append("Password must include at least one uppercase letter.")

    if not re.search(r"[a-z]", password):
        messages.append("Password must include at least one lowercase letter.")

    if not re.search(r"[!@#$%]", password):
        messages.append("Password must include at least one special character from '!@#$%'.")

    if messages:
        return messages
    else:
        return None

# ==========  Verify User Deatils Criteria  ==========

# ==========  Start Admin  ==========
count_products = len(data)
user_query = "SELECT COUNT(*) FROM user_details"
cursor.execute(user_query)
user_result = cursor.fetchone()
count_users = user_result[0] if result else 0

@app.route("/admin")
def home():
    global count_products, count_users, order_count
    items_list = list(enumerate(data))
    products_list = len(data)
    return render_template("admin/home.html",item=items_list, count_products=count_products, count_users=count_users, products_list=products_list, order_count=order_count, products_ordered=products_ordered)

@app.route("/view_products")
def view_products():
    global count_products
    items_list = list(enumerate(data))
    return render_template("admin/products.html",item=items_list, count_products=count_products, count_users=count_users, order_count=order_count, products_ordered=products_ordered)

# ==========  Start Edit Products  ==========
@app.route("/edits/<int:item_index>")
def edits(item_index):
    global count_users, count_products, selected_id
    selected_id = item_index
    select_query = "SELECT * FROM products WHERE id = %s"
    cursor.execute(select_query, (selected_id,))
    current_data = cursor.fetchone()
    
    return render_template("admin/edits.html", item=current_data, count_products=count_products, count_users=count_users)

@app.route('/edit_products', methods=['POST'])
def edit_products():
    global data, selected_id
    if request.method == 'POST':
        
        user_id = selected_id
        new_name = request.form['name']
        new_price = float(request.form['price'])
        new_rating = float(request.form['rating'])
        new_description = request.form['description']
        images_files = request.files['files']
        if images_files:
            file_contents = images_files.read()
            file_base64 = base64.b64encode(file_contents).decode('utf-8')
        else:
            select_query = "SELECT images FROM products WHERE id = %s"
            cursor.execute(select_query, (user_id,))
            current_data = cursor.fetchone()    
            file_base64 = current_data[0]
        
        select_query = "SELECT * FROM products WHERE id = %s"
        cursor.execute(select_query, (user_id,))
        current_data = cursor.fetchone()

        if current_data:
            update_query = (
                "UPDATE products "
                "SET name = %s, price = %s, rating = %s, description = %s, images = %s "
                "WHERE id = %s"
            )
            try:
                cursor.execute(update_query, (new_name, new_price, new_rating, new_description, file_base64, user_id))
                mydata.commit()
            except Exception as e:
                mydata.rollback()
                flash(f"Error Updating Product: {str(e)}", 'error')
        else:
            flash("Product Not Found")
    return redirect(url_for('view_products'))

    
@app.route("/remove_from_products/<int:item_index>")
def remove_from_products(item_index):
    try:
        new_id = item_index
        delete_query = "DELETE FROM products WHERE id = %s"
        cursor.execute(delete_query, (new_id,))
        update_query = "UPDATE products SET id = id - 1 WHERE id > %s"
        cursor.execute(update_query, (new_id,))
        mydata.commit()
        flash("Product removed successfully")
    except Exception as e:
        flash(f"Error removing product: {e}")

    return redirect(url_for('edits'))
# ==========  End Edit Products  ==========

# ==========  Start Add Products  ==========
@app.route("/add")
def add():
    num_id = len(data) + 1
    global count_products, count_users
    return render_template("admin/add.html", num_id=num_id, count_users=count_users, count_products=count_products, order_count=order_count, products_ordered=products_ordered)


@app.route("/add_products", methods=['POST'])
def add_products():
    num_id = len(data) + 1
    if request.method == 'POST':
        new_name = request.form['name']
        new_price = float(request.form['price'])
        new_rating = float(request.form['rating'])
        new_description = request.form['description']

        uploaded_file = request.files['files']
        file_contents = uploaded_file.read()    
        file_base64 = base64.b64encode(file_contents).decode('utf-8')

        query = f"INSERT INTO products (id, name, price, rating, description, images) VALUES ('{num_id}', '{new_name}', '{new_price}', '{new_rating}', '{new_description}', '{file_base64}')"

        try:
            cursor.execute(query)
            mydata.commit()
            flash("Product add successfully")
        except Exception as e:
            mydata.rollback()
            flash(f"Error For Insert Products: {str(e)}", 'error')

    return redirect(url_for('add'))
# ==========  End Add Products  ==========

# ==========  Start Edit User's  ==========
@app.route("/user")
def user():
    global count_users, count_products
    query = "SELECT * FROM user_details"
    cursor.execute(query)
    result = cursor.fetchall()
    user = list(enumerate(result))
    return render_template("admin/user.html",users=user, count_products=count_products, count_users=count_users, order_count=order_count, products_ordered=products_ordered)

@app.route("/edit_users/<int:item_index>")
def edit_users(item_index):
    global count_users, count_products, user_id
    user_id = item_index + 1
    select_query = "SELECT * FROM user_details WHERE id = %s"
    cursor.execute(select_query, (user_id,))
    current_data = cursor.fetchone()

    return render_template("admin/edit_users.html",users=current_data, count_products=count_products, count_users=count_users, order_count=order_count, products_ordered=products_ordered)
    
@app.route("/update_user", methods=['POST'])
def update_user():
    global user_id
    users_id = user_id
    new_first_name = request.form.get("first_name")
    new_last_name = request.form.get("last_name")
    new_number = request.form.get("number")
    new_email = request.form.get("email")
    new_password = request.form.get("password")

    criteria = verify_password(new_password)

    if criteria:
        for message in result:
            flash(message)
    else:
        # Hash the new password if it's not empty
        if new_password:
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        else:
            hashed_password = None  # Set hashed_password to None if no new password is provided

        select_query = "SELECT * FROM user_details WHERE id = %s"
        cursor.execute(select_query, (users_id,))
        current_data = cursor.fetchone()
        if current_data:
            # Check if new password is provided and update the password accordingly
            if hashed_password:
                update_query = (
                    "UPDATE user_details "
                    "SET first_name = %s, last_name = %s, number = %s, email = %s, password = %s "
                    "WHERE id = %s"
                )
                try:
                    cursor.execute(update_query, (new_first_name, new_last_name, new_number, new_email, hashed_password, user_id))
                    print(f"User: {hashed_password}, database: {current_data[5]}")
                    mydata.commit()
                    flash("User updated successfully")
                except Exception as e:
                    flash(f"Error updating user: {e}")
            else:
                # If no new password is provided, update other fields without changing the password
                update_query = (
                    "UPDATE user_details "
                    "SET first_name = %s, last_name = %s, number = %s, email = %s "
                    "WHERE id = %s"
                )
                try:
                    cursor.execute(update_query, (new_first_name, new_last_name, new_number, new_email, user_id))
                    mydata.commit()
                    flash("User updated successfully")
                except Exception as e:
                    flash(f"Error updating user: {e}")
        else:
            flash("User not found")

    return redirect(url_for('user'))

# ==========  Start Edit User's  ==========

# ==========  Start 404 Page  ==========
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', error = e )
# ==========  End 404 Page  ==========

# ==========  End Admin  ==========