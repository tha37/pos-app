from flask import render_template, url_for, flash, redirect, request, jsonify, make_response
from app import app, db, login_manager
from forms import RegistrationForm, LoginForm, ItemForm, SaleForm, OwnerPasswordForm
from models import User, Item, Sale, SaleItem, StockTransaction
from flask_login import login_user, current_user, logout_user, login_required
from sqlalchemy.sql import func
from datetime import datetime, timedelta
import pdfkit
import os
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

UPLOAD_FOLDER = 'static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Home / Dashboard
@app.route("/")
@app.route("/dashboard")
@login_required
def dashboard():
    # Item list for current user
    items = Item.query.filter_by(user_id=current_user.id).all()
    
    # Low stock items for alert
    low_stock_items = Item.query.filter_by(user_id=current_user.id).filter(Item.quantity <= 10).all() # Example threshold
    
    # Sales insights
    today_sales = db.session.query(func.sum(SaleItem.price * SaleItem.quantity)).filter(
        Sale.user_id == current_user.id, Sale.sale_date >= datetime.utcnow().date()
    ).join(Sale).scalar() or 0
    
    # Top-selling item (simple version)
    top_item = db.session.query(Item.name, func.sum(SaleItem.quantity)).filter(
        SaleItem.item_id == Item.id,
        SaleItem.sale.has(user_id=current_user.id)
    ).group_by(Item.name).order_by(func.sum(SaleItem.quantity).desc()).first()

    return render_template('dashboard.html', title='Dashboard', items=items, low_stock_items=low_stock_items, today_sales=today_sales, top_item=top_item)

# User Registration
@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, shop_name=form.shop_name.data, role='owner')
        user.set_password(form.password.data)
        user.set_owner_password(form.owner_password.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

# User Login
@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', title='Login', form=form)

# User Logout
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('login'))

# Add New Item
@app.route("/add_item", methods=['GET', 'POST'])
@login_required
def add_item():
    form = ItemForm()
    if form.validate_on_submit():
        item = Item(user_id=current_user.id, name=form.name.data, quantity=form.quantity.data, unit_price=form.unit_price.data)
        db.session.add(item)
        
        transaction = StockTransaction(user_id=current_user.id, item_id=item.id, type='in', quantity=form.quantity.data)
        db.session.add(transaction)
        db.session.commit()
        flash('Your item has been added!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_item.html', title='Add New Item', form=form)

# New Sale
@app.route("/new_sale", methods=['GET', 'POST'])
@login_required
def new_sale():
    form = SaleForm()
    items = Item.query.filter_by(user_id=current_user.id).all()
    if request.method == 'POST' and form.validate_on_submit():
        item = Item.query.filter_by(user_id=current_user.id, name=form.item_name.data).first()
        if not item or item.quantity < form.quantity.data:
            flash('Not enough stock or item not found!', 'danger')
            return redirect(url_for('new_sale'))

        # Create sale and sale items
        total_price = item.unit_price * form.quantity.data
        sale = Sale(user_id=current_user.id, total_price=total_price)
        db.session.add(sale)
        db.session.flush() # Get the sale id

        sale_item = SaleItem(sale_id=sale.id, item_id=item.id, quantity=form.quantity.data, price=item.unit_price)
        db.session.add(sale_item)
        
        # Update stock
        item.quantity -= form.quantity.data
        
        # Log transaction
        transaction = StockTransaction(user_id=current_user.id, item_id=item.id, type='out', quantity=form.quantity.data)
        db.session.add(transaction)
        db.session.commit()
        
        flash('Sale recorded successfully!', 'success')
        return redirect(url_for('generate_invoice', sale_id=sale.id))
        
    return render_template('new_sale.html', title='New Sale', form=form, items=items)

# Sales Report (Owner Only)
@app.route("/sales_report", methods=['GET', 'POST'])
@login_required
def sales_report():
    if current_user.role != 'owner':
        flash('You do not have permission to view this page.', 'danger')
        return redirect(url_for('dashboard'))

    form = OwnerPasswordForm()
    if form.validate_on_submit():
        if current_user.check_owner_password(form.owner_password.data):
            sales = Sale.query.filter_by(user_id=current_user.id).order_by(Sale.sale_date.desc()).all()
            return render_template('sales_report.html', title='Sales Report', sales=sales)
        else:
            flash('Incorrect password.', 'danger')
    
    return render_template('sales_password_prompt.html', title='Unlock Sales Report', form=form)

# Invoice Generation (PDF)
@app.route("/invoice/<int:sale_id>")
@login_required
def generate_invoice(sale_id):
    sale = Sale.query.filter_by(id=sale_id, user_id=current_user.id).first_or_404()
    sale_items = SaleItem.query.filter_by(sale_id=sale.id).join(Item).add_columns(Item.name).all()
    
    rendered_invoice = render_template('invoice.html', sale=sale, sale_items=sale_items, user=current_user)
    
    # Ensure wkhtmltopdf is installed and in your system's PATH
    config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')
    
    # Save PDF
    pdf = pdfkit.from_string(rendered_invoice, False, configuration=config)
    
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=invoice_{sale.id}.pdf'
    return response

# Logo Upload
@app.route("/settings", methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        if file:
            filename = secure_filename(f"{current_user.id}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            current_user.logo_url = url_for('static', filename=f'images/{filename}')
            db.session.commit()
            flash('Logo updated successfully!', 'success')
            return redirect(url_for('dashboard'))
    return render_template('settings.html', title='Settings', user=current_user)