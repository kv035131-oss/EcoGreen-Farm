# EcoGreen Database Entity-Relationship Diagram

```mermaid
erDiagram
    USER ||--o{ PRODUCT : "lists"
    USER ||--o{ ORDER : "places"
    USER ||--o{ TRANSACTION : "makes"
    USER ||--o{ NOTIFICATION : "receives"
    USER ||--o{ NOTIFICATION_LOG : "audited_in"
    USER ||--o{ REVIEWS : "writes"
    USER ||--o{ SEARCH : "queries"
    PRODUCT ||--o{ PRODUCT_MODERATION_LOG : "has_logs"

    PRODUCT ||--o{ ORDER : "ordered_in"
    PRODUCT ||--o{ REVIEWS : "reviewed_in"

    ORDER ||--o{ TRANSACTION : "settled_by"

    USER {
        int id PK
        string username UK
        string phone_number
        string password
        string email UK
        string user_type
        string status
        datetime created_at
        datetime last_active_at
        string phone
        boolean whatsapp_opt_in
        datetime last_inbound_whatsapp_at
        string notification_language
        boolean flagged
        text flag_note
    }

    PRODUCT {
        int id PK
        int user_id FK
        string name
        float price
        text description
        text image
        string location
        int quantity
        string category
        datetime created_at
        string moderation_status
        text moderation_reason
        datetime moderated_at
        string moderated_by
    }

    PRODUCT_MODERATION_LOG {
        int id PK
        int product_id FK
        string decision
        text reason
        text raw_model_output
        string decided_by
        datetime created_at
    }


    ORDER {
        int id PK
        int product_id FK
        int user_id FK
        float amount
        string phone_number
        string order_status
        datetime confirmed_at
        datetime cancelled_at
        datetime delivered_at
    }

    TRANSACTION {
        int id PK
        int order_id FK
        int user_id FK
        string razorpay_payment_id
        string razorpay_order_id
        string razorpay_signature
        float amount
        string status
        string payment_method
        datetime transaction_date
    }

    NOTIFICATION {
        int id PK
        int user_id FK
        text message
        string type
        boolean is_read
        datetime created_at
    }

    NOTIFICATION_LOG {
        int id PK
        int user_id FK
        string channel
        string event_type
        text message
        string status
        string provider_message_id
        text error
        datetime created_at
    }

    REVIEWS {
        int id PK
        int product_id FK
        int user_id FK
        text comment
        int rating
    }

    SEARCH {
        int id PK
        int user_id FK
        string query
    }
```

## Summary of Tables and Relationships

1. **`User` (table: `user`)**: Central table for all users (Farmers, Consumers, Admins). Holds auth credentials, profile data, and notification preferences.
2. **`Product` (table: `product`)**: Agricultural produce listed by Farmers (`user_id`).
3. **`Order` (table: `order`)**: Purchase records created by Consumers (`user_id`) for specific products (`product_id`).
4. **`Transaction` (table: `transaction`)**: Payment gateway records associated with orders and users.
5. **`Notification` (table: `notification`)**: In-app notifications served to users.
6. **`NotificationLog` (table: `notification_log`)**: Outbox log auditing multi-channel dispatch (WhatsApp Cloud API & Brevo SMTP).
7. **`Reviews` (table: `reviews`)**: Ratings and text reviews submitted by consumers for products.
8. **`Search` (table: `search`)**: Query history logged for analytics search trends.
