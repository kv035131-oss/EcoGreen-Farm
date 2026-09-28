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

---

## 📊 Dedicated Admin Analytics Dashboard & Connecting Power BI

EcoGreen features a dedicated, analytics-only business intelligence dashboard for platform owners accessible at `/admin/dashboard`. When an `admin` user logs in, they are automatically routed to the executive dashboard, hiding consumer/farmer marketplace controls.

### 🛡️ Admin Security & Authentication
- **Web App:** Protected via JWT Bearer Token stored in session and checked by `@admin_required`.
- **Power BI Web Connector:** Supports HTTP Basic Authentication using credentials configured in `.env`:
  ```env
  POWERBI_USER=admin
  POWERBI_PASSWORD=admin123
  ```
- **Data Privacy:** Personal data like phone numbers are masked (`98****1234`) in analytics outputs.

---

### 🔌 Analytics REST API Endpoints (`/api/v1/admin/analytics`)
All endpoints accept optional date filters (`?from=YYYY-MM-DD&to=YYYY-MM-DD` or `?range=7d|30d|90d|all`) and return Power BI-friendly flat JSON:

| Category | Endpoint | Description |
| :--- | :--- | :--- |
| **Overview** | `GET /summary` | Top-level KPIs, revenue, order counts, growth percentages vs prior period. |
| **Orders & Revenue** | `GET /orders-over-time?interval=day\|week\|month` | Time series order volume, revenue, and average order value. |
| | `GET /order-status-breakdown` | Counts by status (Pending, Confirmed, Delivered, Cancelled, Rejected). |
| | `GET /fulfillment-funnel` | Drop-off metrics across Placed → Paid → Confirmed → Delivered. |
| | `GET /abandoned-orders` | Unpaid abandoned order count, revenue lost, and top 20 list. |
| **Farmer Analytics** | `GET /farmer-performance?limit=10` | Orders received, accepted, rejected, response time, and revenue per farmer. |
| | `GET /farmer-response-time` | Average, median, and bucketed farmer confirmation response times. |
| | `GET /inactive-farmers?days=30` | List of farmers with no listings or confirmations in the past X days. |
| | `GET /top-farmers-by-revenue?limit=10` | Top revenue-generating farmers leaderboard. |
| **Consumer Analytics**| `GET /top-consumers?limit=10` | Top buyers by order count and total spend in INR (₹). |
| | `GET /new-vs-returning?interval=month` | Cohort breakdown of new vs returning customers over time. |
| | `GET /repeat-purchase` | Repeat purchase rate %, total ordering buyers, avg orders per buyer. |
| **Products & Stock** | `GET /category-breakdown` | Sales, revenue, and average price split by produce category. |
| | `GET /top-products?limit=10` | Best-selling farm produce items ranked by revenue. |
| | `GET /supply-vs-demand` | Stock listed vs units sold and sell-through percentage per category. |
| | `GET /low-stock?threshold=10` | Low-stock and out-of-stock inventory alerts. |
| | `GET /dead-stock?days=30` | Products listed with zero sales in the specified window. |
| **Geography & Time** | `GET /sales-by-location` | Revenue, orders, and farmer density grouped by region/district. |
| | `GET /orders-by-weekday` | Order distribution across days of the week (Mon–Sun). |
| | `GET /orders-by-hour` | Order volume by hour of the day (00:00–23:00). |
| | `GET /orders-heatmap` | 7x24 weekday × hour matrix for demand intensity heatmaps. |
| **Growth & Payments**| `GET /user-growth?interval=month` | New and cumulative farmers and consumers over time. |
| | `GET /payments-breakdown` | Transaction counts and amounts by status (Success, Failed, Created). |
| | `GET /payment-methods` | Revenue split by payment method (UPI, Card, Netbanking, Wallet). |

---

### 📈 Step-by-Step Guide: Connecting Power BI Desktop

To build interactive reports in **Power BI Desktop**:

1. **Open Power BI Desktop** and click **Get Data > Web**.
2. **Select Basic Authentication** in the connection dialog:
   - **User name:** `admin`
   - **Password:** `admin123`
3. **Add Queries for Each Table:**
   Enter the desired endpoint URL (e.g., `http://127.0.0.1:5000/api/v1/admin/analytics/summary` or `http://127.0.0.1:5000/api/v1/admin/analytics/orders-over-time`).
4. **Transform & Convert to Table:**
   In Power Query Editor, click **To Table**, expand the JSON record columns, and set appropriate data types (Currency, Whole Number, DateTime).
5. **Schedule Refresh:** Set up scheduled refresh in Power BI Service using Web Connection credentials.

---

### 🛠️ CLI Commands

- **Create Admin User:**
  ```bash
  flask create-admin --username admin --email admin@ecogreen.com --password admin123
  ```

- **Seed Realistic Indian Demo Data:**
  ```bash
  flask seed-demo-data
  ```
  Generates 12 Indian farmers, 30 consumers, 50 produce items, and ~250 orders over the past 90 days with realistic status variations, response times, payment methods, and inventory alerts.

1. Sign up / Log in to [Razorpay Dashboard](https://dashboard.razorpay.com/).
2. Switch to **Test Mode** using the toggle in the top navbar.
3. Go to **Account & Settings** → **API Keys** under Website and App settings.
4. Click **Generate Test Key** and copy `Key ID` and `Key Secret` into your `.env` file.
5. (Optional Webhooks): Go to **Settings** → **Webhooks** → **Add New Webhook**, enter your webhook URL (`http://<your-domain>/api/v1/payments/webhook`), select `payment.captured`, and copy the secret.

### 3. Razorpay Test Sandbox Credentials
When testing through Razorpay Checkout modal in Test Mode, use these details:

| Payment Method | Test Card / Info | Expiry / CVV / Details |
| :--- | :--- | :--- |
| **Card (Success)** | `4111 1111 1111 1111` | Any future date (e.g. `12/30`), CVV `123`, OTP `123456` |
| **Card (Failure)** | `4000 0000 0000 0002` | Any future date, CVV `123` |
| **UPI / VPA** | `success@razorpay` | Auto-approves payment |

---

## 🧪 Testing Endpoints (curl / Postman)

### 1. Create Payment Order (`POST /pay`)
```bash
curl -X POST http://localhost:5000/pay \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_CONSUMER_JWT_TOKEN>" \
  -d '{"order_id": 1}'
```
* **Response (Live Mode):** Returns `razorpay_order_id`, `amount` (in paise), and `key_id`.
* **Response (Simulated Mode):** Immediately updates Transaction & Order status to `Paid` and returns `simulate: true`.

### 2. Verify Signature (`POST /api/v1/payments/verify`)
```bash
curl -X POST http://localhost:5000/api/v1/payments/verify \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_CONSUMER_JWT_TOKEN>" \
  -d '{
    "razorpay_order_id": "order_1234567890",
    "razorpay_payment_id": "pay_1234567890",
    "razorpay_signature": "generated_hmac_sha256_signature"
  }'
```

### 3. Simulate Webhook with Valid HMAC Signature (`POST /api/v1/payments/webhook`)
You can test the server webhook endpoint locally using Python to generate a valid HMAC signature:

**Python Script (`simulate_webhook.py`):**
```python
import hmac, hashlib, requests, json

webhook_secret = "your_webhook_secret_key" # matches RAZORPAY_WEBHOOK_SECRET
payload = {
    "event": "payment.captured",
    "payload": {
        "payment": {
            "entity": {
                "id": "pay_test_999",
                "order_id": "order_test_123",
                "amount": 5000,
                "currency": "INR",
                "status": "captured"
            }
        }
    }
}

body_bytes = json.dumps(payload).encode('utf-8')
signature = hmac.new(webhook_secret.encode('utf-8'), body_bytes, hashlib.sha256).hexdigest()

headers = {
    'Content-Type': 'application/json',
    'X-Razorpay-Signature': signature
}

res = requests.post("http://localhost:5000/api/v1/payments/webhook", data=body_bytes, headers=headers)
print("Webhook status code:", res.status_code)
print("Response:", res.json())
```

---

## 📊 Connecting Power BI

EcoGreen features a dedicated Admin Analytics module under `/api/v1/admin/analytics` optimized for **Power BI Desktop** via its native **Web (REST API)** data source. 

### 1. Admin Credentials & Access Control
- Default Admin Account: `admin` (or `admin@ecogreen.com`)
- Default Admin Password: `admin123`
- Create / Update Admin Account via CLI:
  ```bash
  flask create-admin --username admin --email admin@ecogreen.com --password admin123
  ```

### 2. How to Connect in Power BI Desktop
1. Open **Power BI Desktop**.
2. Click **Get Data** → **Web** (under Common data sources).
3. Select **Basic** radio button, enter the target analytics endpoint URL (e.g. `http://localhost:5000/api/v1/admin/analytics/summary`), and click **OK**.
4. When prompted for Access Credentials:
   - Select **Basic** on the left menu.
   - Enter User name: `admin` (or `admin@ecogreen.com`)
   - Enter Password: `admin123`
   - Select Level: `http://localhost:5000/api/v1/admin/analytics`
   - Click **Connect**.
5. Power BI will parse the flat JSON response directly into a data table.
6. **Repeat step 2-4** for each analytics endpoint. Add them as separate Power BI queries (`Summary`, `OrdersOverTime`, `TopFarmers`, `TopProducts`, `CategoryBreakdown`, `UserGrowth`), then build relationships and visual dashboards inside Power BI's data model.

---

### 🧪 Admin Analytics Endpoint `curl` Examples (Basic Auth)

#### 1. Platform Summary KPIs
```bash
curl -u "admin:admin123" http://localhost:5000/api/v1/admin/analytics/summary
```
**Response:**
```json
{
  "confirmed_orders": 10,
  "paid_orders": 12,
  "pending_orders": 5,
  "total_consumers": 25,
  "total_farmers": 8,
  "total_orders": 15,
  "total_products_listed": 18,
  "total_revenue": 450.0,
  "total_transactions_failed": 1,
  "total_transactions_success": 12,
  "unpaid_orders": 3
}
```

#### 2. Orders Over Time (Daily / Weekly / Monthly)
```bash
curl -u "admin:admin123" "http://localhost:5000/api/v1/admin/analytics/orders-over-time?interval=day"
```
**Response:**
```json
[
  { "period": "2026-09-27", "order_count": 15, "revenue": 450.0 }
]
```

#### 3. Top Farmers by Revenue
```bash
curl -u "admin:admin123" "http://localhost:5000/api/v1/admin/analytics/top-farmers?limit=10"
```
**Response:**
```json
[
  { "farmer_id": 2, "farmer_name": "ajay_farmer", "total_orders": 15, "total_revenue": 450.0 }
]
```

#### 4. Top Performing Produce
```bash
curl -u "admin:admin123" "http://localhost:5000/api/v1/admin/analytics/top-products?limit=10"
```
**Response:**
```json
[
  { "category": "Vegetables", "product_id": 1, "product_name": "Fresh Organic Tomatoes", "units_sold": 10, "revenue": 150.0 }
]
```

#### 5. Produce Category Breakdown
```bash
curl -u "admin:admin123" http://localhost:5000/api/v1/admin/analytics/category-breakdown
```
**Response:**
```json
[
  { "category": "Vegetables", "order_count": 10, "revenue": 300.0 },
  { "category": "Dairy & Eggs", "order_count": 5, "revenue": 150.0 }
]
```

#### 6. User Signup Growth over Time
```bash
curl -u "admin:admin123" "http://localhost:5000/api/v1/admin/analytics/user-growth?interval=day"
```
**Response:**
```json
[
  { "new_consumers": 25, "new_farmers": 8, "period": "2026-09-27" }
]
```

---

## 📱 WhatsApp Notifications System

EcoGreen includes a multi-language **WhatsApp Notification Engine** with a built-in **SIMULATE mode** so all features work out-of-the-box with zero credentials required.

- WhatsApp provider: Meta Cloud API (setup instructions coming)

---

## 📧 Brevo SMTP Email Notifications

EcoGreen supports transactional email delivery to farmers and consumers via **Brevo SMTP Relay** (formerly Sendinblue).

### Brevo Setup Instructions:
1. **Create a free Brevo account:** Sign up at [brevo.com](https://www.brevo.com).
2. **Get SMTP Credentials:** Go to **Transactional** > **SMTP & API** in your Brevo dashboard and copy your **SMTP Key**.
3. **Verify Sender Email (Important):**
   > [!IMPORTANT]
   > In Brevo Dashboard under **Senders & IP**, make sure the email address you set in `SENDER_EMAIL` is **added and verified as an authorized sender**. Brevo will reject emails sent from unverified email addresses with a 550 sender error.
4. **Configure `.env`**:
   ```env
   EMAIL_NOTIFY_MODE=smtp
   SMTP_SERVER=smtp-relay.brevo.com
   SMTP_PORT=587
   SMTP_USERNAME=your_brevo_login_email@domain.com
   SMTP_PASSWORD=your_brevo_smtp_key
   SENDER_EMAIL=your_verified_sender@domain.com
   ```
5. **Test Delivery & Diagnostics:**
   - CLI Test: Run `python send_test_email.py <recipient_email>` to test transmission and view detailed SMTP status codes.
   - Set Farmer Email: Run `python set_farmer_email.py <email_address>` to update farmer Ajay's email in the database.


## 📜 License

This project is licensed under the [MIT License](LICENSE).



