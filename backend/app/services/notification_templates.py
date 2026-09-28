"""
EcoGreen Multi-Language WhatsApp Notification Templates
Languages supported: en (English), hi (Hindi), kn (Kannada), ta (Tamil), te (Telugu), ml (Malayalam)
Designed with emojis and simple syntax for low-literacy clarity.
"""

TEMPLATES = {
    'order_placed_farmer': {
        'en': "🛒 New Order #{order_id}: {quantity} kg {product_name} from {consumer_name}. Reply 1 to ACCEPT ✅ or 2 to REJECT ❌.",
        'hi': "🛒 नया ऑर्डर #{order_id}: {quantity} किग्रा {product_name} ग्राहक {consumer_name} से। स्वीकार करने के लिए 1 ✅ या अस्वीकार करने के लिए 2 ❌ भेजें।",
        'kn': "🛒 ಹೊಸ ಆದೇಶ #{order_id}: {quantity} ಕೆಜಿ {product_name} ({consumer_name}). ಸ್ವೀಕರಿಸಲು 1 ✅ ಅಥವಾ ತಿರಸ್ಕರಿಸಲು 2 ❌ ಎಂದು ಪ್ರತ್ಯುತ್ತರಿಸಿ.",
        'ta': "🛒 புதிய ஆர்டர் #{order_id}: {quantity} கிலோ {product_name} ({consumer_name}). ஏற்க 1 ✅ அல்லது நிராகரிக்க 2 ❌ என பதிலளிக்கவும்.",
        'te': "🛒 కొత్త ఆర్డర్ #{order_id}: {quantity} కేజీల {product_name} ({consumer_name}). ఆమోదించడానికి 1 ✅ లేదా తిరస్కరించడానికి 2 ❌ అని రిప్లై ఇవ్వండి.",
        'ml': "🛒 പുതിയ ഓർഡർ #{order_id}: {quantity} കിലോ {product_name} ({consumer_name}). സ്വീകരിക്കാൻ 1 ✅ നിരസിക്കാൻ 2 ❌ എന്ന് മറുപടി നൽകുക."
    },
    'payment_success_consumer': {
        'en': "✅ Payment Successful! Receipt #{receipt_no} for ₹{amount} for Order #{order_id} ({product_name}). Thank you for buying fresh from EcoGreen farmers!",
        'hi': "✅ भुगतान सफल! ऑर्डर #{order_id} ({product_name}) के लिए ₹{amount} की रसीद #{receipt_no}। इकोग्रीन किसानों से ताजा खरीदने के लिए धन्यवाद!",
        'kn': "✅ ಪಾವತಿ ಯಶಸ್ವಿಯಾಗಿದೆ! ಆದೇಶ #{order_id} ಗೆ ₹{amount} ಸ್ವೀಕೃತಿ. EcoGreen ಧನ್ಯವಾದಗಳು!",
        'ta': "✅ பணம் செலுத்தப்பட்டது! ஆர்டர் #{order_id} தொகை ₹{amount}. நன்றி!",
        'te': "✅ చెల్లింపు పూర్తయింది! ఆర్డర్ #{order_id} మొత్తం ₹{amount}. ధన్యవాదాలు!",
        'ml': "✅ പേയ്‌മെന്റ് വിജയകരം! ഓർഡർ #{order_id} തുക ₹{amount}. നന്ദി!"
    },
    'payment_success_farmer': {
        'en': "💰 Payment Received! ₹{amount} collected for Order #{order_id} ({product_name}) from {consumer_name}.",
        'hi': "💰 भुगतान प्राप्त हुआ! ग्राहक {consumer_name} से ऑर्डर #{order_id} के लिए ₹{amount} प्राप्त हुए।",
        'kn': "💰 ಪಾವತಿ ಸ್ವೀಕರಿಸಲಾಗಿದೆ! ಆದೇಶ #{order_id} ಗೆ ₹{amount}.",
        'ta': "💰 பணம் பெறப்பட்டது! ஆர்டர் #{order_id} தொகை ₹{amount}.",
        'te': "💰 చెల్లింపు అందింది! ఆర్డర్ #{order_id} మొత్తం ₹{amount}.",
        'ml': "💰 തുക ലഭിച്ചു! ഓർഡർ #{order_id} തുക ₹{amount}."
    },
    'order_accepted_consumer': {
        'en': "✅ Great news! Farmer {farmer_name} HAS ACCEPTED your Order #{order_id} ({product_name}). It is being prepared for delivery.",
        'hi': "✅ खुशखबरी! किसान {farmer_name} ने आपका ऑर्डर #{order_id} स्वीकार कर लिया है। डिलीवरी की तैयारी जारी है।",
        'kn': "✅ ಶುಭ ಸುದ್ದಿ! ರೈತ {farmer_name} ನಿಮ್ಮ ಆದೇಶ #{order_id} ಅನ್ನು ಸ್ವೀಕರಿಸಿದ್ದಾರೆ.",
        'ta': "✅ மகிழ்ச்சியான செய்தி! விவசாயி {farmer_name} உங்கள் ஆர்டர் #{order_id} ஐ ஏற்றுக்கொண்டார்.",
        'te': "✅ శుభవార్త! రైతు {farmer_name} మీ ఆర్డర్ #{order_id} ని ఆమోదించారు.",
        'ml': "✅ നല്ല വാർത്ത! കർഷകൻ {farmer_name} നിങ്ങളുടെ ഓർഡർ #{order_id} സ്വീകരിച്ചു."
    },
    'order_rejected_consumer': {
        'en': "❌ Update on Order #{order_id}: Farmer {farmer_name} is unable to fulfill your order. Any payment made will be refunded.",
        'hi': "❌ अपडेट: किसान {farmer_name} आपका ऑर्डर #{order_id} पूरा करने में असमर्थ हैं। आपका भुगतान वापस कर दिया जाएगा।",
        'kn': "❌ ಆದೇಶ #{order_id} ಅಪ್‌ಡೇಟ್: ರೈತ {farmer_name} ಪೂರೈಸಲು ಸಾಧ್ಯವಾಗುತ್ತಿಲ್ಲ.",
        'ta': "❌ ஆர்டர் #{order_id} செய்தி: விவசாயியால் நிறைவேற்ற முடியவில்லை.",
        'te': "❌ ఆర్డర్ #{order_id} అప్‌డేట్: రైతు రద్దు చేశారు.",
        'ml': "❌ ഓർഡർ #{order_id} അപ്‌ഡേറ്റ്: കർഷകന് പൂർത്തിയാക്കാൻ സാധിച്ചില്ല."
    },
    'order_delivered_consumer': {
        'en': "📦 Delivered! Your Order #{order_id} ({product_name}) has been delivered. Enjoy your fresh produce!",
        'hi': "📦 डिलीवर हो गया! आपका ऑर्डर #{order_id} ({product_name}) डिलीवर हो चुका है। ताजी उपज का आनंद लें!",
        'kn': "📦 ತಲುಪಿಸಲಾಗಿದೆ! ನಿಮ್ಮ ಆದೇಶ #{order_id} ತಲುಪಿದೆ.",
        'ta': "📦 விநியோகிக்கப்பட்டது! உங்கள் ஆர்டர் #{order_id} சேர்ந்தது.",
        'te': "📦 డెలివరీ అయింది! మీ ఆర్డర్ #{order_id} పూర్తయింది.",
        'ml': "📦 ഡെലിവർ ചെയ്തു! നിങ്ങളുടെ ഓർഡർ #{order_id} എത്തിച്ചേർന്നു."
    },
    'farmer_order_reminder': {
        'en': "⏰ Pending Reminder: Order #{order_id} ({quantity} kg {product_name}) from {consumer_name} is waiting for your response. Reply 1 to ACCEPT ✅ or 2 to REJECT ❌.",
        'hi': "⏰ रिमाइंडर: ऑर्डर #{order_id} ({product_name}) आपकी प्रतिक्रिया का इंतजार कर रहा है। स्वीकार करने के लिए 1 ✅ या अस्वीकार के लिए 2 ❌ भेजें।",
        'kn': "⏰ ಜ್ಞಾಪನೆ: ಆದೇಶ #{order_id} ನಿಮ್ಮ ಉತ್ತರಕ್ಕಾಗಿ ಕಾಯುತ್ತಿದೆ. ಸ್ವೀಕರಿಸಲು 1 ✅ ಅಥವಾ ತಿರಸ್ಕರಿಸಲು 2 ❌.",
        'ta': "⏰ நினைவூட்டல்: ஆர்டர் #{order_id} உங்கள் பதிலுக்காக காத்திருக்கிறது.",
        'te': "⏰ రిమైండర్: ఆర్డర్ #{order_id} మీ స్పందన కోసం వేచి ఉంది.",
        'ml': "⏰ റിമൈൻഡർ: ഓർഡർ #{order_id} നിങ്ങളുടെ മറുപടിക്കായി കാത്തിരിക്കുന്നു."
    },
    'low_stock_farmer': {
        'en': "⚠️ Low Stock Alert! Product '{product_name}' has only {quantity} units remaining. Update your stock on EcoGreen to keep selling!",
        'hi': "⚠️ कम स्टॉक अलर्ट! उत्पाद '{product_name}' का केवल {quantity} बचा है। इकोग्रीन पर स्टॉक अपडेट करें!",
        'kn': "⚠️ ಕಡಿಮೆ ಸ್ಟಾಕ್ ಹೆಚ್ಚರಿಕೆ! '{product_name}' ಕೇವಲ {quantity} ಉಳಿದಿದೆ.",
        'ta': "⚠️ குறைந்த இருப்பு! '{product_name}' {quantity} மட்டுமே உள்ளது.",
        'te': "⚠️ స్టాక్ తక్కువగా ఉంది! '{product_name}' కేవలం {quantity} మిగిలి ఉంది.",
        'ml': "⚠️ കുറഞ്ഞ സ്റ്റോക്ക് മുന്നറിയിപ്പ്! '{product_name}' {quantity} മാത്രം ബാക്കി."
    },
    'welcome_opt_in': {
        'en': "🎉 Welcome to EcoGreen WhatsApp Notifications! {join_instruction}",
        'hi': "🎉 इकोग्रीन व्हाट्सएप नोटिफिकेशन में आपका स्वागत है! {join_instruction}",
        'kn': "🎉 EcoGreen WhatsApp ಸೂಚನೆಗಳಿಗೆ ಸ್ವಾಗತ! {join_instruction}",
        'ta': "🎉 EcoGreen வாட்ஸ்அப் அறிவிப்புகளுக்கு நல்வரவு! {join_instruction}",
        'te': "🎉 EcoGreen వాట్సాప్ నోటిಫికేషన్‌లకు స్వాగతం! {join_instruction}",
        'ml': "🎉 EcoGreen വാട്ട്‌സ്ആപ്പ് നോട്ടിഫിക്കേഷനുകളിലേക്ക് സ്വാഗതം! {join_instruction}"
    },
    'test_message': {
        'en': "🧪 Test Notification: EcoGreen WhatsApp service is working perfectly on your device!",
        'hi': "🧪 परीक्षण संदेश: इकोग्रीन व्हाट्सएप सेवा आपके डिवाइस पर पूरी तरह काम कर रही है!",
        'kn': "🧪 ಪರೀಕ್ಷಾ ಸಂದೇಶ: EcoGreen WhatsApp ಸೇವೆ ಸರಿಯಾಗಿ ಕೆಲಸ ಮಾಡುತ್ತಿದೆ!",
        'ta': "🧪 சோதனை செய்தி: EcoGreen வாட்ஸ்அப் சேவை நன்றாக வேலை செய்கிறது!",
        'te': "🧪 పరీక్ష సందేశం: EcoGreen వాట్సాప్ సేవ సరిగ్గా పనిచేస్తోంది!",
        'ml': "🧪 ടെസ്റ്റ് സന്ദേശം: EcoGreen വാട്ട്‌സ്ആപ്പ് സേവനം വിജയകരമാണ്!"
    }
}

def render_message(event_type: str, lang: str = 'en', **kwargs) -> str:
    """Renders a notification template in the specified language."""
    if event_type not in TEMPLATES:
        return f"EcoGreen Notification [{event_type}]: {kwargs}"
    
    lang_templates = TEMPLATES[event_type]
    template = lang_templates.get(lang, lang_templates.get('en', ''))
    
    try:
        return template.format(**kwargs)
    except KeyError:
        return template
