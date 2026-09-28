# EcoGreen API Reference Manual

Complete list of all RESTful API endpoints available in the EcoGreen platform.

## 1. Authentication & User Management (`/api/v1/`)

| Method | Endpoint | Role Required | Request Body / Params | Description |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/User/create` | Public | `{username, email, password, user_type, phone_number}` | Register a new user (farmer or consumer) |
| `POST` | `/api/v1/Login` | Public | `{username, password}` | Authenticate user and receive JWT access token |
| `GET` | `/api/v1/user/profile` | Authenticated | Header `Authorization: Bearer <token>` | Retrieve current logged-in user profile |
| `GET` | `/api/v1/User` | Admin | Query `?page=1&per_page=10` | Paginated listing of registered users |

---

## 2. Product Management & Search

| Method | Endpoint | Role Required | Request Body / Params | Description |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/products/create` | Farmer | `{user_id, name, price, quantity, category, location, description}` | Create a new produce listing |
| `GET` | `/api/v1/products` | Public | Query `?page=1&per_page=50` | Paginated listing of all active produce items |
| `GET` | `/api/v1/products/<int:id>` | Public | Path parameter `id` | View detailed product specifications and reviews |
| `POST` | `/api/v1/Search` | Public | `{user_id, keyword}` | Search products by name/category and log query |

---

## 3. Order Processing & Status Lifecycle

| Method | Endpoint | Role Required | Request Body / Params | Description |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/Orders/create` | Consumer | `{product_id, user_id, amount, phone_number}` | Place a new produce purchase order |
| `GET` | `/api/v1/Orders` | Authenticated | Header `Authorization: Bearer <token>` | List orders relevant to the current user |
| `GET` | `/api/v1/Orders/<int:user_id>`| Authenticated | Path parameter `user_id` | View order history for specific user |
| `PUT`, `POST` | `/api/v1/Orders/<id>/status`| Farmer | `{status: "Confirmed" / "Rejected" / "Cancelled"}` | Update order status and trigger notifications |
| `PUT`, `POST` | `/api/v1/Orders/<id>/deliver`| Farmer | None | Mark order as Delivered and log completion |

---

## 4. Payment Gateway (Razorpay Integration)

| Method | Endpoint | Role Required | Request Body / Params | Description |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/pay` | Consumer | `{order_id, amount}` | Initialize Razorpay payment order |
| `POST` | `/api/v1/payments/verify` | Consumer | `{razorpay_order_id, razorpay_payment_id, razorpay_signature}` | Verify HMAC SHA256 payment signature |
| `POST` | `/api/v1/payments/webhook` | System / Webhook | Razorpay Webhook Payload | Process asynchronous payment events |

---

## 5. Multi-Channel Notifications & Admin Outbox

| Method | Endpoint | Role Required | Request Body / Params | Description |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/notifications` | Authenticated | Header `Authorization: Bearer <token>` | Fetch in-app notifications for user |
| `PUT` | `/api/v1/notifications/<id>/read` | Authenticated | Path parameter `notification_id` | Mark individual notification as read |
| `PUT` | `/api/v1/notifications/read-all` | Authenticated | Header `Authorization: Bearer <token>` | Mark all user notifications as read |
| `POST` | `/api/v1/notifications/opt-in` | Authenticated | `{whatsapp_opt_in: true, phone, language}` | Update WhatsApp notification preferences |
| `POST` | `/api/v1/notifications/test` | Authenticated | `{to_phone, message}` | Dispatch test WhatsApp notification |
| `GET` | `/api/v1/admin/notifications/logs` | Admin | Query `?page=1&channel=all&status=all` | Audit outbox log records |
| `GET` | `/api/v1/admin/notifications/stats` | Admin | None | Summary statistics of notification channels |
| `POST` | `/api/v1/admin/notifications/test-email` | Admin | `{recipient_email}` | Test Brevo SMTP relay dispatch |
| `GET`, `POST`| `/api/v1/notifications/whatsapp/webhook` | Meta Webhook | Verification token / Webhook payload | Meta WhatsApp Cloud API webhook listener |

---

## 6. Executive Business Intelligence & Analytics (`/api/v1/admin/analytics/`)

| Method | Endpoint | Role Required | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/summary` | Admin | KPI summary (Revenue, Orders, Active Farmers, Customers) |
| `GET` | `/orders-over-time` | Admin | Daily revenue & order volume trends |
| `GET` | `/order-status-breakdown` | Admin | Distribution of order statuses (Delivered, Pending, etc.) |
| `GET` | `/category-breakdown` | Admin | Revenue & volume grouped by product category |
| `GET` | `/top-products` | Admin | Top 10 selling produce items by revenue |
| `GET` | `/top-farmers-by-revenue`| Admin | Highest revenue generating farmers |
| `GET` | `/farmer-performance` | Admin | Detailed performance metrics per farmer |
| `GET` | `/top-consumers` | Admin | Top spending consumer accounts |
| `GET` | `/user-growth` | Admin | Cumulative user registration growth curves |
| `GET` | `/payment-methods` | Admin | Breakdown of payment methods used |
| `GET` | `/sales-by-location` | Admin | Geographic distribution of sales |
| `GET` | `/low-stock` | Admin | Inventory alerts for products below threshold |
| `GET` | `/dead-stock` | Admin | Products with zero sales over past 30+ days |
| `GET` | `/fulfillment-funnel` | Admin | Order conversion and drop-off funnel rates |
| `GET` | `/farmer-response-time`| Admin | Average hours taken by farmers to confirm orders |
| `GET` | `/orders-by-hour` | Admin | Hourly distribution of order placements |
| `GET` | `/orders-by-weekday` | Admin | Day-of-week sales volume analysis |
| `GET` | `/orders-heatmap` | Admin | Hour vs Day order frequency matrix |
| `GET` | `/repeat-purchase` | Admin | Percentage of repeat customer orders |
| `GET` | `/new-vs-returning` | Admin | Monthly new vs returning customer revenue |
| `GET` | `/inactive-farmers` | Admin | Farmers with no active listings in 30+ days |
| `GET` | `/abandoned-orders` | Admin | Pending orders with unpaid status |
