import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from server.models import db, User, Product, Order, Transaction, Reviews

INDIAN_FARMERS = [
    {"name": "ramesh_patel", "email": "ramesh.patel@nashikfarms.in", "phone": "9823011223", "location": "Nashik, Maharashtra"},
    {"name": "suresh_kumar", "email": "suresh.kumar@mahabubnagar.in", "phone": "9440122334", "location": "Mahabubnagar, Telangana"},
    {"name": "ananya_sharma", "email": "ananya.sharma@punefarms.in", "phone": "9822433445", "location": "Pune, Maharashtra"},
    {"name": "vijay_verma", "email": "vijay.verma@shimlaorchards.in", "phone": "9816055667", "location": "Shimla, Himachal Pradesh"},
    {"name": "priya_reddy", "email": "priya.reddy@gunturchilli.in", "phone": "9848077889", "location": "Guntur, Andhra Pradesh"},
    {"name": "gurpreet_singh", "email": "gurpreet.singh@karnalgrains.in", "phone": "9812099001", "location": "Karnal, Punjab"},
    {"name": "rajesh_gowda", "email": "rajesh.gowda@mysuruorganics.in", "phone": "9845011223", "location": "Mysuru, Karnataka"},
    {"name": "vikram_shah", "email": "vikram.shah@ananddairy.in", "phone": "9898033445", "location": "Anand, Gujarat"},
    {"name": "sunita_deshmukh", "email": "sunita.deshmukh@nagpurcitrus.in", "phone": "9422155667", "location": "Nagpur, Maharashtra"},
    {"name": "arvind_hegde", "email": "arvind.hegde@ratnagirimango.in", "phone": "9448077889", "location": "Ratnagiri, Maharashtra"},
    {"name": "devadas_nair", "email": "devadas.nair@wayanadspices.in", "phone": "9447099001", "location": "Wayanad, Kerala"},
    {"name": "manoj_joshi", "email": "manoj.joshi@indorefarm.in", "phone": "9826012345", "location": "Indore, Madhya Pradesh"}
]

INDIAN_CONSUMERS = [
    "aarav_gupta", "aditi_rao", "amit_sharma", "anika_singh", "arjun_mehta",
    "bhavna_joshi", "deepak_verma", "divya_nair", "harsh_patel", "ishita_roy",
    "karan_malhotra", "kavita_desai", "manish_kumar", "meera_iyer", "neha_chawla",
    "nikhil_bansal", "pooja_kapoor", "rahul_sen", "riya_kulkarni", "rohan_saxena",
    "sakshi_bhatia", "sanjay_mishra", "shreya_agarwal", "siddharth_reddy", "sneha_tripathi",
    "swati_dube", "tanvi_thakur", "varun_nambiar", "yash_choudhary", "zara_khan"
]

PRODUCT_TEMPLATES = [
    # Vegetables
    {"name": "Fresh Red Tomatoes (10kg Box)", "cat": "Vegetables", "price": 320.0, "qty": 45, "img": "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=500"},
    {"name": "Organic Crisp Carrots (5kg)", "cat": "Vegetables", "price": 180.0, "qty": 30, "img": "https://images.unsplash.com/photo-1598170845058-32b9d6a5da37?w=500"},
    {"name": "Farm Fresh Spinach (Palak 3 Bunches)", "cat": "Vegetables", "price": 60.0, "qty": 50, "img": "https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=500"},
    {"name": "Green Cauliflower & Broccoli Pack", "cat": "Vegetables", "price": 140.0, "qty": 25, "img": "https://images.unsplash.com/photo-1568584711075-3d021a7c3ca3?w=500"},
    {"name": "Fresh Green Capsicum (2kg)", "cat": "Vegetables", "price": 110.0, "qty": 35, "img": "https://images.unsplash.com/photo-1563565375-f3fdfdbefa83?w=500"},
    {"name": "Green Peas (Matar 5kg)", "cat": "Vegetables", "price": 250.0, "qty": 40, "img": "https://images.unsplash.com/photo-1587735243615-c03f25aaff15?w=500"},
    {"name": "Organic Onions (10kg Bag)", "cat": "Vegetables", "price": 280.0, "qty": 60, "img": "https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?w=500"},
    {"name": "Highland Potatoes (10kg Bag)", "cat": "Vegetables", "price": 240.0, "qty": 5, "img": "https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=500"}, # Low stock
    {"name": "Fresh Sweet Corn (6 Cobs)", "cat": "Vegetables", "price": 90.0, "qty": 3, "img": "https://images.unsplash.com/photo-1551754655-cd27e38d2076?w=500"}, # Low stock
    {"name": "Bitter Gourd / Karela (2kg)", "cat": "Vegetables", "price": 85.0, "qty": 40, "img": "https://images.unsplash.com/photo-1603048588665-791ca8aea617?w=500"},

    # Fruits
    {"name": "Alphonso Mangoes (1 Dozen)", "cat": "Fruits", "price": 850.0, "qty": 20, "img": "https://images.unsplash.com/photo-1553279768-865429fa0078?w=500"},
    {"name": "Crisp Shimla Apples (5kg)", "cat": "Fruits", "price": 650.0, "qty": 25, "img": "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=500"},
    {"name": "Fresh Sweet Pomegranates (3kg)", "cat": "Fruits", "price": 420.0, "qty": 18, "img": "https://images.unsplash.com/photo-1615485290382-441e4d049cb5?w=500"},
    {"name": "Nagpur Juicy Oranges (5kg)", "cat": "Fruits", "price": 350.0, "qty": 30, "img": "https://images.unsplash.com/photo-1547514701-42782101795e?w=500"},
    {"name": "Robusta Bananas (1 Dozen)", "cat": "Fruits", "price": 70.0, "qty": 50, "img": "https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=500"},
    {"name": "Fresh Mahabaleshwar Strawberries (500g)", "cat": "Fruits", "price": 220.0, "qty": 15, "img": "https://images.unsplash.com/photo-1464965911861-746a04b4bca6?w=500"},
    {"name": "Papaya Sweet Honey (2 Units)", "cat": "Fruits", "price": 120.0, "qty": 2, "img": "https://images.unsplash.com/photo-1517282009859-f000ec3b26fe?w=500"}, # Low stock
    {"name": "Seedless Black Grapes (2kg)", "cat": "Fruits", "price": 260.0, "qty": 22, "img": "https://images.unsplash.com/photo-1537640538966-79f369143f8f?w=500"},

    # Dairy & Eggs
    {"name": "A2 Pure Desi Cow Ghee (1 Litre Jar)", "cat": "Dairy & Eggs", "price": 1450.0, "qty": 25, "img": "https://images.unsplash.com/photo-1589927986089-35812388d1f4?w=500"},
    {"name": "Raw Wildflower Honey (1kg)", "cat": "Dairy & Eggs", "price": 550.0, "qty": 30, "img": "https://images.unsplash.com/photo-1587049352846-4a222e784d38?w=500"},
    {"name": "Farm Fresh Free-Range Eggs (30 Tray)", "cat": "Dairy & Eggs", "price": 240.0, "qty": 40, "img": "https://images.unsplash.com/photo-1516467508483-a7212febe31a?w=500"},
    {"name": "Organic Malai Paneer (1kg Block)", "cat": "Dairy & Eggs", "price": 420.0, "qty": 20, "img": "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=500"},
    {"name": "Fresh White Butter (Makhan 500g)", "cat": "Dairy & Eggs", "price": 280.0, "qty": 15, "img": "https://images.unsplash.com/photo-1589985270826-4b7bb135bc9d?w=500"},
    {"name": "Pure Desi Cow Milk (5 Litres Can)", "cat": "Dairy & Eggs", "price": 320.0, "qty": 35, "img": "https://images.unsplash.com/photo-1550583724-b2692b85b150?w=500"},

    # Grains & Spices
    {"name": "Aromatic Basmati Rice (5kg Bag)", "cat": "Grains & Spices", "price": 680.0, "qty": 30, "img": "https://images.unsplash.com/photo-1586201375761-83865001e31c?w=500"},
    {"name": "Organic Lakadong Turmeric Powder (500g)", "cat": "Grains & Spices", "price": 220.0, "qty": 35, "img": "https://images.unsplash.com/photo-1615485290382-441e4d049cb5?w=500"},
    {"name": "Guntur Red Chilli Powder (1kg)", "cat": "Grains & Spices", "price": 340.0, "qty": 28, "img": "https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=500"},
    {"name": "Pure Wayanad Black Pepper (500g)", "cat": "Grains & Spices", "price": 450.0, "qty": 20, "img": "https://images.unsplash.com/photo-1509358271058-acd01cc9386a?w=500"},
    {"name": "Cold-Pressed Mustard Oil (2 Litres)", "cat": "Grains & Spices", "price": 390.0, "qty": 25, "img": "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=500"},
    {"name": "Organic Whole Wheat Atta (10kg Bag)", "cat": "Grains & Spices", "price": 440.0, "qty": 50, "img": "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=500"},
    {"name": "Exotic Cardamom Pods / Elaichi (250g)", "cat": "Grains & Spices", "price": 950.0, "qty": 0, "img": "https://images.unsplash.com/photo-1509358271058-acd01cc9386a?w=500"} # Dead / Out of stock
]

def seed_demo_data():
    pwd_hash = generate_password_hash('pass123')

    # 1. Create Admin if not existing
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@ecogreen.com',
            password=generate_password_hash('admin123'),
            user_type='admin',
            status='Active',
            phone_number='9999999999',
            created_at=datetime.utcnow() - timedelta(days=120),
            last_active_at=datetime.utcnow()
        )
        db.session.add(admin)
    db.session.commit()

    # 2. Create Farmers
    farmer_objs = []
    for f in INDIAN_FARMERS:
        u = User.query.filter_by(username=f['name']).first()
        if not u:
            # Vary farmer registration dates over last 120 days
            created_days_ago = random.randint(30, 120)
            u = User(
                username=f['name'],
                email=f['email'],
                password=pwd_hash,
                user_type='farmer',
                status='Active',
                phone_number=f['phone'],
                created_at=datetime.utcnow() - timedelta(days=created_days_ago),
                last_active_at=datetime.utcnow() - timedelta(days=random.randint(0, 15))
            )
            db.session.add(u)
        farmer_objs.append(u)
    db.session.commit()

    # Make 2 farmers inactive for testing inactive farmers API
    if len(farmer_objs) >= 2:
        farmer_objs[-1].last_active_at = datetime.utcnow() - timedelta(days=45)
        farmer_objs[-2].last_active_at = datetime.utcnow() - timedelta(days=50)
        db.session.commit()

    # 3. Create Consumers
    consumer_objs = []
    for idx, cname in enumerate(INDIAN_CONSUMERS):
        u = User.query.filter_by(username=cname).first()
        if not u:
            created_days_ago = random.randint(5, 110)
            u = User(
                username=cname,
                email=f"{cname}@gmail.com",
                password=pwd_hash,
                user_type='consumer',
                status='Active',
                phone_number=f"9876{idx:06d}",
                created_at=datetime.utcnow() - timedelta(days=created_days_ago),
                last_active_at=datetime.utcnow() - timedelta(days=random.randint(0, 5))
            )
            db.session.add(u)
        consumer_objs.append(u)
    db.session.commit()

    # 4. Create Products
    product_objs = []
    for idx, ptmpl in enumerate(PRODUCT_TEMPLATES):
        # Assign products to farmers evenly
        farmer = farmer_objs[idx % len(farmer_objs)]
        existing = Product.query.filter_by(name=ptmpl['name'], user_id=farmer.id).first()
        if not existing:
            created_days_ago = random.randint(15, 90)
            # Create dead stock test: product listed 45 days ago with 0 recent orders
            if "Dead" in ptmpl.get("name", ""):
                created_days_ago = 50

            p = Product(
                user_id=farmer.id,
                name=ptmpl['name'],
                price=ptmpl['price'],
                description=f"Fresh high quality {ptmpl['name']} directly harvested from {farmer.username}'s farm in {INDIAN_FARMERS[idx % len(INDIAN_FARMERS)]['location']}.",
                image=ptmpl['img'],
                location=INDIAN_FARMERS[idx % len(INDIAN_FARMERS)]['location'],
                quantity=ptmpl['qty'],
                category=ptmpl['cat'],
                created_at=datetime.utcnow() - timedelta(days=created_days_ago)
            )
            db.session.add(p)
            product_objs.append(p)
        else:
            product_objs.append(existing)
    db.session.commit()

    # 5. Create ~250 Orders over the last 90 days
    if Order.query.count() < 100:
        now = datetime.utcnow()
        statuses = ['Delivered', 'Confirmed', 'Pending', 'Cancelled', 'Rejected']
        status_weights = [60, 20, 10, 5, 5]

        payment_methods = ['upi', 'card', 'netbanking', 'wallet']
        pm_weights = [55, 25, 12, 8]

        for i in range(260):
            days_ago = random.randint(0, 89)
            hour = random.choices(
                list(range(24)),
                weights=[1, 1, 1, 1, 2, 3, 5, 8, 12, 14, 15, 12, 10, 9, 11, 13, 15, 16, 14, 10, 7, 4, 2, 1]
            )[0]
            minute = random.randint(0, 59)

            trans_date = now - timedelta(days=days_ago, hours=(now.hour - hour) % 24, minutes=minute)

            consumer = random.choice(consumer_objs)
            # Pick product (avoiding dead stock product for 200 orders so it remains dead stock)
            product = random.choice(product_objs[:-1]) if i < 240 else product_objs[-1]

            status = random.choices(statuses, weights=status_weights)[0]
            pm_method = random.choices(payment_methods, weights=pm_weights)[0]

            is_paid = (status in ['Delivered', 'Confirmed']) or (status == 'Pending' and random.random() > 0.4)
            payment_status = 'Paid' if is_paid else 'Unpaid'

            # Timestamps
            conf_at = None
            canc_at = None
            deliv_at = None

            if status in ['Confirmed', 'Delivered']:
                resp_minutes = random.randint(15, 360) # 15m to 6h response time
                conf_at = trans_date + timedelta(minutes=resp_minutes)
            if status == 'Delivered':
                deliv_minutes = random.randint(1200, 2880) # 20h to 48h delivery time
                deliv_at = conf_at + timedelta(minutes=deliv_minutes)
            elif status in ['Cancelled', 'Rejected']:
                resp_minutes = random.randint(30, 480)
                canc_at = trans_date + timedelta(minutes=resp_minutes)

            order = Order(
                product_id=product.id,
                user_id=consumer.id,
                amount=round(product.price * random.choice([1, 1, 2, 3]), 2),
                mpesa_receipt_number=f"RZP-{random.randint(1000000, 9999999)}",
                merchant_request_id=f"MR-{i:04d}",
                checkout_request_id=f"CR-{i:04d}",
                result_code=0 if is_paid else 1,
                result_desc='Success' if is_paid else 'Pending Payment',
                order_status=status,
                payment_status=payment_status,
                phone_number=consumer.phone_number or "9876543210",
                transaction_date=trans_date,
                confirmed_at=conf_at,
                cancelled_at=canc_at,
                delivered_at=deliv_at
            )
            db.session.add(order)
            db.session.flush()

            # Create corresponding Transaction record
            txn_status = 'Success' if is_paid else ('Failed' if status in ['Cancelled', 'Rejected'] else 'Created')
            txn = Transaction(
                order_id=order.id,
                razorpay_order_id=f"order_{random.randint(100000, 999999)}",
                razorpay_payment_id=f"pay_{random.randint(100000, 999999)}" if is_paid else None,
                razorpay_signature="simulated_sig" if is_paid else None,
                amount=order.amount,
                currency="INR",
                status=txn_status,
                payment_method=pm_method,
                created_at=trans_date,
                updated_at=trans_date
            )
            db.session.add(txn)

            # Add sample review for ~30% of delivered orders
            if status == 'Delivered' and random.random() < 0.3:
                rev = Reviews(
                    product_id=product.id,
                    user_id=consumer.id,
                    comment=random.choice([
                        "Very fresh produce, delivered on time!",
                        "Excellent quality organic vegetables from the farmer.",
                        "Good packaging and prompt delivery.",
                        "Authentic taste, highly recommended!",
                        "Satisfied with the purchase."
                    ]),
                    rating=random.choice([4, 5, 5, 5, 3])
                )
                db.session.add(rev)

        db.session.commit()

    print("Demo data seeded successfully!")
