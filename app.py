import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import stripe

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this to a random string in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ebooks.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB max upload
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'epub', 'mobi'}

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Stripe configuration
stripe.api_key = "your_stripe_secret_key"  # Replace with your actual key
STRIPE_PUBLIC_KEY = "your_stripe_public_key"  # Replace with your actual key

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    is_admin = db.Column(db.Boolean, default=False)
    cart = db.relationship('CartItem', backref='user', lazy=True)
    favorites = db.relationship('Favorite', backref='user', lazy=True)
    purchases = db.relationship('Purchase', backref='user', lazy=True)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    author = db.Column(db.String(100))
    description = db.Column(db.Text)
    price = db.Column(db.Float)
    file_path = db.Column(db.String(255))
    cover_image = db.Column(db.String(255))
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    cart_items = db.relationship('CartItem', backref='book', lazy=True)
    favorites = db.relationship('Favorite', backref='book', lazy=True)
    purchases = db.relationship('Purchase', backref='book', lazy=True)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    transaction_id = db.Column(db.String(100))
    amount = db.Column(db.Float)
    date_purchased = db.Column(db.DateTime, default=datetime.utcnow)

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    books = Book.query.order_by(Book.date_added.desc()).all()
    current_year = datetime.utcnow().year  # Get the current year
    return render_template('index.html', books=books, current_year=current_year)


@app.route('/search')
def search():
    query = request.args.get('query', '')
    books = Book.query.filter(Book.title.contains(query) | Book.description.contains(query)).all()
    return render_template('search_results.html', books=books, query=query)

@app.route('/book/<int:book_id>')
def book_detail(book_id):
    book = Book.query.get_or_404(book_id)
    return render_template('book_detail.html', book=book)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        phone = request.form.get('phone')
        password = request.form.get('password')
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already exists.')
            return redirect(url_for('signup'))
        
        new_user = User(email=email, 
                      name=name, 
                      phone=phone, 
                      password=generate_password_hash(password, method='pbkdf2:sha256'))
        
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        return redirect(url_for('index'))
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.password, password):
            flash('Please check your login details and try again.')
            return redirect(url_for('login'))
        
        login_user(user)
        return redirect(url_for('index'))
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/add_to_cart/<int:book_id>')
@login_required
def add_to_cart(book_id):
    book = Book.query.get_or_404(book_id)
    
    # Check if already in cart
    cart_item = CartItem.query.filter_by(user_id=current_user.id, book_id=book_id).first()
    if cart_item:
        flash('This book is already in your cart.')
        return redirect(url_for('book_detail', book_id=book_id))
    
    # Check if already purchased
    purchase = Purchase.query.filter_by(user_id=current_user.id, book_id=book_id).first()
    if purchase:
        flash('You already own this book.')
        return redirect(url_for('book_detail', book_id=book_id))
    
    cart_item = CartItem(user_id=current_user.id, book_id=book_id)
    db.session.add(cart_item)
    db.session.commit()
    
    flash('Book added to cart.')
    return redirect(url_for('cart'))

@app.route('/remove_from_cart/<int:item_id>')
@login_required
def remove_from_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    
    if cart_item.user_id != current_user.id:
        flash('Unauthorized action.')
        return redirect(url_for('cart'))
    
    db.session.delete(cart_item)
    db.session.commit()
    
    flash('Item removed from cart.')
    return redirect(url_for('cart'))

@app.route('/cart')
@login_required
def cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum([item.book.price for item in cart_items])
    
    return render_template('cart.html', cart_items=cart_items, total=total, 
                          stripe_public_key=STRIPE_PUBLIC_KEY)

@app.route('/add_to_favorites/<int:book_id>')
@login_required
def add_to_favorites(book_id):
    # Check if already in favorites
    favorite = Favorite.query.filter_by(user_id=current_user.id, book_id=book_id).first()
    if favorite:
        flash('This book is already in your favorites.')
        return redirect(url_for('book_detail', book_id=book_id))
    
    favorite = Favorite(user_id=current_user.id, book_id=book_id)
    db.session.add(favorite)
    db.session.commit()
    
    flash('Book added to favorites.')
    return redirect(url_for('favorites'))

@app.route('/remove_from_favorites/<int:favorite_id>')
@login_required
def remove_from_favorites(favorite_id):
    favorite = Favorite.query.get_or_404(favorite_id)
    
    if favorite.user_id != current_user.id:
        flash('Unauthorized action.')
        return redirect(url_for('favorites'))
    
    db.session.delete(favorite)
    db.session.commit()
    
    flash('Book removed from favorites.')
    return redirect(url_for('favorites'))

@app.route('/favorites')
@login_required
def favorites():
    favorites = Favorite.query.filter_by(user_id=current_user.id).all()
    return render_template('favorites.html', favorites=favorites)

@app.route('/create_checkout_session', methods=['POST'])
@login_required
def create_checkout_session():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    
    if not cart_items:
        flash('Your cart is empty.')
        return redirect(url_for('cart'))
    
    line_items = []
    for item in cart_items:
        line_items.append({
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': item.book.title,
                },
                'unit_amount': int(item.book.price * 100),  # Convert to cents
            },
            'quantity': 1,
        })
    
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=url_for('checkout_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('cart', _external=True),
        )
        
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        flash(f'An error occurred: {str(e)}')
        return redirect(url_for('cart'))

@app.route('/checkout_success')
@login_required
def checkout_success():
    session_id = request.args.get('session_id', '')
    
    if not session_id:
        return redirect(url_for('index'))
    
    try:
        # Retrieve session information
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        
        # Process the purchase
        cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
        
        for item in cart_items:
            # Create purchase record
            purchase = Purchase(
                user_id=current_user.id,
                book_id=item.book.id,
                transaction_id=session_id,
                amount=item.book.price
            )
            db.session.add(purchase)
            db.session.delete(item)  # Remove from cart
        
        db.session.commit()
        flash('Purchase completed successfully!')
        return redirect(url_for('purchases'))
    except Exception as e:
        flash(f'Error completing purchase: {str(e)}')
        return redirect(url_for('cart'))

@app.route('/purchases')
@login_required
def purchases():
    purchases = Purchase.query.filter_by(user_id=current_user.id).order_by(Purchase.date_purchased.desc()).all()
    return render_template('purchases.html', purchases=purchases)

@app.route('/download/<int:book_id>')
@login_required
def download(book_id):
    # Check if user has purchased the book
    purchase = Purchase.query.filter_by(user_id=current_user.id, book_id=book_id).first()
    
    if not purchase and not current_user.is_admin:
        flash('You have not purchased this book.')
        return redirect(url_for('book_detail', book_id=book_id))
    
    book = Book.query.get_or_404(book_id)
    filename = os.path.basename(book.file_path)
    
    return send_from_directory(
        os.path.join(app.root_path, 'uploads'),
        filename,
        as_attachment=True
    )

# Admin routes
@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('index'))
    
    return render_template('admin/dashboard.html')

@app.route('/admin/books')
@login_required
def admin_books():
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('index'))
    
    books = Book.query.all()
    return render_template('admin/books.html', books=books)

@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('index'))
    
    users = User.query.filter_by(is_admin=False).all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/sales')
@login_required
def admin_sales():
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('index'))
    
    sales = Purchase.query.order_by(Purchase.date_purchased.desc()).all()
    total_revenue = sum([sale.amount for sale in sales])
    
    return render_template('admin/sales.html', sales=sales, total_revenue=total_revenue)

@app.route('/admin/add_book', methods=['GET', 'POST'])
@login_required
def add_book():
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        description = request.form.get('description')
        price = float(request.form.get('price'))
        
        # Handle ebook file
        ebook_file = request.files.get('ebook_file')
        if not ebook_file or not allowed_file(ebook_file.filename):
            flash('Invalid ebook file. Allowed types: pdf, epub, mobi')
            return redirect(url_for('add_book'))
        
        ebook_filename = secure_filename(ebook_file.filename)
        ebook_path = os.path.join(app.config['UPLOAD_FOLDER'], ebook_filename)
        ebook_file.save(ebook_path)
        
        # Handle cover image
        cover_path = ''
        cover_image = request.files.get('cover_image')
        if cover_image and '.' in cover_image.filename and cover_image.filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png', 'gif'}:
            cover_filename = secure_filename(cover_image.filename)
            cover_path = os.path.join(app.config['UPLOAD_FOLDER'], cover_filename)
            cover_image.save(cover_path)
        
        new_book = Book(
            title=title,
            author=author,
            description=description,
            price=price,
            file_path=ebook_path,
            cover_image=cover_path if cover_path else None
        )
        
        db.session.add(new_book)
        db.session.commit()
        
        flash('Book added successfully!')
        return redirect(url_for('admin_books'))
    
    return render_template('admin/add_book.html')

@app.route('/admin/edit_book/<int:book_id>', methods=['GET', 'POST'])
@login_required
def edit_book(book_id):
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('index'))
    
    book = Book.query.get_or_404(book_id)
    
    if request.method == 'POST':
        book.title = request.form.get('title')
        book.author = request.form.get('author')
        book.description = request.form.get('description')
        book.price = float(request.form.get('price'))
        
        # Update ebook file if provided
        ebook_file = request.files.get('ebook_file')
        if ebook_file and ebook_file.filename and allowed_file(ebook_file.filename):
            ebook_filename = secure_filename(ebook_file.filename)
            ebook_path = os.path.join(app.config['UPLOAD_FOLDER'], ebook_filename)
            ebook_file.save(ebook_path)
            book.file_path = ebook_path
        
        # Update cover image if provided
        cover_image = request.files.get('cover_image')
        if cover_image and cover_image.filename and '.' in cover_image.filename and cover_image.filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png', 'gif'}:
            cover_filename = secure_filename(cover_image.filename)
            cover_path = os.path.join(app.config['UPLOAD_FOLDER'], cover_filename)
            cover_image.save(cover_path)
            book.cover_image = cover_path
        
        db.session.commit()
        flash('Book updated successfully!')
        return redirect(url_for('admin_books'))
    
    return render_template('admin/edit_book.html', book=book)

@app.route('/admin/delete_book/<int:book_id>')
@login_required
def delete_book(book_id):
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('index'))
    
    book = Book.query.get_or_404(book_id)
    
    # Delete associated records
    CartItem.query.filter_by(book_id=book_id).delete()
    Favorite.query.filter_by(book_id=book_id).delete()
    
    # Note: We don't delete purchase records to maintain sales history
    
    # Delete file if it exists
    if book.file_path and os.path.exists(book.file_path):
        os.remove(book.file_path)
    
    # Delete cover if it exists
    if book.cover_image and os.path.exists(book.cover_image):
        os.remove(book.cover_image)
    
    db.session.delete(book)
    db.session.commit()
    
    flash('Book deleted successfully!')
    return redirect(url_for('admin_books'))

# Initialize db
with app.app_context():
    db.create_all()
    # Create admin user if none exists
    admin = User.query.filter_by(is_admin=True).first()
    if not admin:
        admin = User(
            email='admin@example.com',
            name='Admin',
            password=generate_password_hash('admin123', method='pbkdf2:sha256'),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)