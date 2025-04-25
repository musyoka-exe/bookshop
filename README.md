# E-Book Store

A streamlined Python-based e-commerce platform for selling ebooks, built with Flask.

## Features

### Customer Features
- User registration and login
- Browse and search for books
- View book details
- Add books to cart
- Add books to favorites/wishlist
- Secure checkout with Stripe
- Download purchased books

### Admin Features
- Book management (add, edit, delete)
- User management
- Sales monitoring and reporting

## Installation and Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Step 1: Clone the repository

```bash
git clone https://github.com/musyoka-exe/bookshop.git
cd ebook-store
```

### Step 2: Set up a virtual environment

```bash
python -m venv venv
```

Activate the virtual environment:

- On Windows:
```bash
venv\Scripts\activate
```

- On macOS/Linux:
```bash
source venv/bin/activate
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure environment variables

Create a `.env` file in the project root and add the following:

```
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your_secret_key
STRIPE_PUBLIC_KEY=your_stripe_public_key
STRIPE_SECRET_KEY=your_stripe_secret_key
```

Replace the placeholder values with your actual keys.

### Step 5: Initialize the database

```bash
flask run
```

The database will be automatically created on first run.

### Step 6: Access the application

Open your browser and navigate to `http://127.0.0.1:5000`

## Default Admin Account

- Email: admin@example.com
- Password: admin123

Change these credentials immediately after first login!

## Directory Structure

```
ebook-store/
│
├── app.py                  # Main application file
├── uploads/                # Folder for ebook files and covers
│   
├── templates/              # HTML templates
│   ├── admin/              # Admin panel templates
│   │   ├── dashboard.html
│   │   ├── books.html
│   │   ├── users.html
│   │   ├── sales.html
│   │   ├── add_book.html
│   │   └── edit_book.html
│   │
│   ├── base.html           # Base template with layout
│   ├── index.html          # Homepage
│   ├── login.html
│   ├── signup.html
│   ├── book_detail.html
│   ├── cart.html
│   ├── favorites.html
│   ├── purchases.html
│   ├── search_results.html
│   └── checkout_success.html
│
└── requirements.txt        # Python dependencies
```

## Dependencies

- Flask - Web framework
- Flask-SQLAlchemy - ORM for database operations
- Flask-Login - User authentication
- Werkzeug - Utilities
- Stripe - Payment processing
- Bootstrap - Frontend styling (via CDN)
- Font Awesome - Icons (via CDN)

## Security Considerations

- Passwords are securely hashed using Werkzeug's security functions
- File uploads are sanitized and restricted to allowed file types
- Payment processing is handled by Stripe for PCI compliance
- User authentication is required for all sensitive operations
- Admin-only areas are protected from unauthorized access

## Note About Payment Processing

This application uses Stripe for payment processing. In a production environment, you should:

1. Use HTTPS for all communications
2. Set up proper webhook handling for payment events
3. Implement additional security measures as recommended by Stripe

Credits
engineer musyoka mutunga(geomatics, gis, survey, rs, ai, ml)

## License

[MIT License](LICENSE)
