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

## 💳 Razorpay Payment Integration

EcoGreen integrates **Razorpay** for payment processing. Payment state (`Unpaid` → `Paid`) is tracked independently from order status (`Pending` → `Confirmed`). An order is marked `Paid` only after a verified server-side Razorpay signature check or webhook event.

### 1. Environment & Configuration
Create a `.env` file in the project root:
```env
RAZORPAY_KEY_ID=rzp_test_your_key_id
RAZORPAY_KEY_SECRET=your_razorpay_secret_key
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret_key
RAZORPAY_SIMULATE=true
```

* **`RAZORPAY_SIMULATE=true`**: Enables simulated instant payments for local testing without active Razorpay API keys.
* Set `RAZORPAY_SIMULATE=false` when using live or test sandbox credentials from Razorpay.

### 2. Getting Test API Keys from Razorpay Dashboard
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

## 📜 License

This project is licensed under the [MIT License](LICENSE).


