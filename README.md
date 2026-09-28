# EcoGreen - Direct Farmer to Consumer Platform

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Framework-Flask_3.0-green.svg)](https://flask.palletsprojects.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

EcoGreen is a direct-to-consumer agricultural e-commerce platform that eliminates middlemen, allowing local farmers to list fresh produce directly for consumers with automated WhatsApp notifications, Brevo SMTP email relays, Razorpay payment gateway integration, and real-time executive business intelligence dashboards.

---

## 🌟 Key Features by Role

### 🌾 Farmers
- **Produce Management**: Create, view, update, and manage fresh produce listings with location, category, pricing, and stock levels.
- **Order Lifecycle Management**: Receive instant notifications for incoming orders with 1-click status updates (Confirm, Reject, Deliver).
- **Automated Reminders**: Receive automated 6-hour pending order reminders via background APScheduler jobs.

### 🛒 Consumers
- **Marketplace Browsing**: Search and filter fresh farm produce by category, keyword, and location.
- **Razorpay Checkout**: Seamless online payments supporting UPI, Cards, Netbanking, and Wallets with automatic signature verification.
- **Order Tracking & Notifications**: Track order status and receive real-time updates via WhatsApp and In-App notifications.

### 👑 Administrators
- **Executive BI Analytics**: 22 dedicated business intelligence endpoints covering revenue trends, order funnels, dead stock, low stock, farmer response times, and geographic distribution.
- **Multi-Channel Outbox Audit**: Monitor and inspect WhatsApp Cloud API and Brevo SMTP email dispatch logs and success rates.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.12, Flask, Flask-SQLAlchemy, Flask-JWT-Extended, Flask-Migrate, APScheduler
- **Database**: SQLite (Development/Test), PostgreSQL-ready ORM schema
- **Frontend**: HTML5, Vanilla CSS3 (Custom Design Tokens), JavaScript (ES6+ Vanilla API Client Wrapper)
- **External Services**: Razorpay Payments API, Meta WhatsApp Cloud API, Brevo SMTP Email Relay

---

## 📂 Repository Directory Structure

```
ecogreen/
├── backend/                       # Python Flask backend application
│   ├── app/                       # Core application package
│   │   ├── __init__.py            # Application factory create_app()
│   │   ├── config.py              # Environment configurations (Dev, Prod, Test)
│   │   ├── extensions.py          # SQLAlchemy, Migrate, JWT extension instances
│   │   ├── cli/                   # Flask CLI commands (create-admin, seed-demo-data)
│   │   ├── models/                # Domain SQLAlchemy models (user, product, order, etc.)
│   │   ├── routes/                # Domain Flask Blueprints (auth, products, orders, etc.)
│   │   ├── services/              # Business logic, payment, notification, & email services
│   │   └── utils/                 # Decorators (admin_required), validators, and helpers
│   └── requirements.txt           # Python dependency requirements
├── database/                      # Database migrations, seed scripts, & ER diagram
│   ├── ER_DIAGRAM.md              # Mermaid Entity-Relationship diagram
│   ├── instance/                  # SQLite database storage directory
│   ├── migrations/                # Alembic / Flask-Migrate database migrations
│   └── seeds/                     # Demo data generator and test scripts
├── frontend/                      # User interface templates and static assets
│   ├── static/                    # CSS stylesheets, JavaScript modules, & images
│   │   ├── css/                   # Base, component, and per-role stylesheets
│   │   └── js/                    # API client wrapper, auth logic, and app scripts
│   └── templates/                 # Jinja2 HTML templates grouped by role
│       ├── admin/                 # Executive analytics dashboard templates
│       ├── auth/                  # Login and registration templates
│       ├── consumer/              # Marketplace and consumer order templates
│       ├── farmer/                # Farmer produce dashboard templates
│       └── shared/                # Shared base, navbar, and footer components
├── docs/                          # Comprehensive technical documentation
│   ├── API_REFERENCE.md           # Detailed endpoint specifications for all 53 routes
│   ├── ARCHITECTURE.md            # System architecture and request flow diagrams
│   └── screenshots/               # Application UI screenshots
├── tests/                         # Pytest automated unit and integration tests
├── .env.example                   # Environment configuration template
├── README.md                      # Project documentation and setup guide
└── run.py                         # Application entry point script
```

---

## 🚀 Quickstart & Setup Guide

### 1. Clone & Setup Virtual Environment
```bash
git clone https://github.com/kv035131-oss/Distance-calculator-using-ultrasonic-sensor.git ecogreen
cd ecogreen
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env` and fill in your keys:
```bash
cp .env.example .env
```

### 4. Database Setup & Migration
```bash
python -m flask --app run.py db upgrade
```

### 5. Seed Demo Data & Create Admin
```bash
python -m flask --app run.py seed-demo-data
python -m flask --app run.py create-admin --username admin --password admin123
```

### 6. Run Application Locally
```bash
python run.py
```
Open your browser at `http://127.0.0.1:5000` to access EcoGreen.

---

## 🧪 Running Automated Tests

Run the full pytest suite:
```bash
pytest
```

---

## 🖼️ UI Screenshots Placeholder

| Marketplace | Executive BI Dashboard |
| :---: | :---: |
| ![Marketplace](docs/screenshots/marketplace.png) | ![Admin Dashboard](docs/screenshots/admin_dashboard.png) |
