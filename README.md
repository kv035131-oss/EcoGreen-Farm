# 🌾 EcoGreen — Direct Farmer-to-Consumer Platform

**EcoGreen** is a full-stack digital web application designed to connect local farmers directly with consumers. By eliminating traditional middlemen and intermediaries, the platform empowers farmers to get fair prices for their produce while enabling consumers to purchase high-quality, fresh organic food at lower prices.

---

## 🎯 Core Value Proposition

* **Direct Market Access for Farmers:** Farmers can list their harvest (vegetables, fruits, honey, eggs, dairy, etc.) with custom pricing, images, stock quantities, and farm location details.
* **Cost Savings for Consumers:** Buyers purchase farm-fresh produce directly from verified local growers.
* **Order & Role-Based Workflow:** 
  * Consumers browse products, select quantities, and place orders via **Mpesa Express STK Push** payment prompt.
  * Orders start in **`Pending`** status until the listing farmer reviews and clicks **"Confirm Order"** on their private dashboard.
* **Strict Order Privacy:** Each user (farmer or consumer) only sees order data relevant to their account.

---

## 👥 User Roles & Workflow

### 1. 🧑‍🌾 Farmers (Sellers)
* **Account Registration:** Register as a `Farmer`.
* **List Produce:** Publish fresh produce items specifying Name, Unit Price, Stock Quantity, Location, Image URL, and Farming Method Description.
* **Farmer Order Dashboard:** View incoming orders specifically placed for their farm produce.
* **Order Confirmation:** Review pending customer orders and click **"Confirm Order"** to approve them.

### 2. 🛒 Consumers (Buyers)
* **Account Registration:** Register as a `Consumer`.
* **Explore Market:** Filter produce by category (*Vegetables*, *Fruits*, *Dairy & Eggs*, or *All*), search keywords, and view unit prices and stock.
* **Order Produce:** Select quantity, provide delivery notes and Mpesa phone number.
* **Private Orders Tracker:** Monitor private order status (*Pending* → *Confirmed*) on their personal dashboard.

---

## 🛠️ Technology Stack

| Layer | Technologies & Tools |
| :--- | :--- |
| **Backend Framework** | Python 3.x, Flask |
| **Database & ORM** | SQLAlchemy (SQLite / PostgreSQL), Flask-Migrate |
| **Authentication & Security** | Flask-JWT-Extended (JWT Bearer tokens), Werkzeug Password Hashing |
| **Payments Integration** | Mpesa Express API (Safaricom STK Push integration) |
| **Media & Assets** | Cloudinary API, Unsplash Presets |
| **Frontend UI** | HTML5, Vanilla CSS, FontAwesome 6, Google Fonts (Inter & Outfit) |

---

## 🔌 API Endpoints Summary

### Authentication & Users
* `POST /api/v1/User/create` — Register a new account (`farmer` or `consumer`) and issue a JWT token.
* `POST /api/v1/Login` — Authenticate credentials and retrieve access token.
* `GET /api/v1/user/profile` — Fetch profile details of the authenticated user.

### Products & Produce Market
* `GET /api/v1/products` — Retrieve all available farm produce sorted by newest listing first.
* `POST /api/v1/products/create` — Publish a new farm produce listing.
* `GET /api/v1/products/<id>` — View detailed info, ratings, and reviews for a single produce item.
* `POST /api/v1/Search` — Search produce by keywords.

### Orders & Payments
* `POST /api/v1/Orders/create` — Place a new customer produce order.
* `GET /api/v1/Orders/<user_id>` — Retrieve private role-filtered orders for the logged-in user.
* `POST /api/v1/Orders/<order_id>/status` — Farmer endpoint to update order status to `Confirmed`.
* `POST /pay` — Trigger Mpesa Express STK Push payment prompt to customer phone.

---

## ⚡ How to Run Locally

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Start Application Server:**
   ```bash
   python run.py
   ```
3. **Access Application:** Open `http://localhost:5000` in your web browser.

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

