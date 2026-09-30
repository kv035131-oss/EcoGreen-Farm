import os, re

root = r'c:\Users\kv035\Downloads\Farmer-to-Consumer-App-main\Farmer-to-Consumer-App-main'
templates_dir = os.path.join(root, 'frontend', 'templates')

def clean_template(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Remove i18n script tags
    content = re.sub(r'<script\s+src=[\'\"][^\'\"]*i18n\.js[\'\"]>\s*</script>\n?', '', content)

    # 2. Remove data-i18n and data-i18n-placeholder attributes (preserving whitespace cleanly)
    content = re.sub(r'\s+data-i18n=[\'\"][^\'\"]*[\'\"]', '', content)
    content = re.sub(r'\s+data-i18n-placeholder=[\'\"][^\'\"]*[\'\"]', '', content)

    # 3. Remove language switcher elements
    # In navbar.html: <button onclick="setLanguage('kn')" ...>ಕನ್ನಡ</button>
    content = re.sub(r'<button\s+onclick=[\'\"]setLanguage\(\'kn\'\)[\'\"].*?>.*?</button>\s*', '', content, flags=re.DOTALL)
    # In index.html: <div ... id="lang-switcher">...</div>
    content = re.sub(r'<div[^>]*id=[\'\"]lang-switcher[\'\"].*?</div>\s*', '', content, flags=re.DOTALL)

    # 4. Replace window.t calls in index.html JS logic if present
    if 'index.html' in filepath:
        content = content.replace("const tPowerBi = window.t('nav.power_bi');", "const tPowerBi = 'Power BI Analytics';")
        content = content.replace("const tListProd = window.t('nav.list_product');", "const tListProd = 'List Produce';")
        content = content.replace("const tLogin = window.t('nav.login');", "const tLogin = 'Log In';")
        content = content.replace("const tNoProduce = window.t('product.no_produce');", "const tNoProduce = 'No Produce Found';")
        content = content.replace("const tNoProduceDesc = window.t('product.no_produce_desc');", "const tNoProduceDesc = 'Try adjusting your search query or filter categories to find farm produce.';")
        content = content.replace("const tListProduce = window.t('nav.list_product');", "const tListProduce = 'List Produce';")
        content = content.replace("const tDelete = window.t('product.delete');", "const tDelete = 'Delete';")
        content = content.replace("const tPending = window.t('product.pending_review');", "const tPending = 'Pending Review';")
        content = content.replace("const tOrderNow = window.t('product.order_now');", "const tOrderNow = 'Order Now';")
        
        content = content.replace("const stockText = window.t('product.in_stock', {count: p.quantity});", "const stockText = `${p.quantity} in stock`;")
        content = content.replace("const confirmMsg = window.t('product.delete_confirm', {name: productName});", "const confirmMsg = `Are you sure you want to delete \"${productName}\"?`;")
        content = content.replace("document.getElementById('orderProductStock').textContent = window.t('product.in_stock', {count: product.quantity});", "document.getElementById('orderProductStock').textContent = `${product.quantity} in stock`;")
        
        content = content.replace("document.getElementById('authTitle').textContent = window.t('auth.login_title');", "document.getElementById('authTitle').textContent = 'User Login';")
        content = content.replace("document.getElementById('authSubmitBtn').textContent = window.t('auth.sign_in_btn');", "document.getElementById('authSubmitBtn').textContent = 'Sign In';")
        content = content.replace("document.getElementById('authToggleText').textContent = window.t('auth.no_account');", "document.getElementById('authToggleText').textContent = \"Don't have an account?\";")
        content = content.replace("document.getElementById('authToggleBtn').textContent = window.t('auth.register_now');", "document.getElementById('authToggleBtn').textContent = 'Register Now';")
        
        content = content.replace("document.getElementById('authTitle').textContent = window.t('auth.register_title');", "document.getElementById('authTitle').textContent = 'Create Account';")
        content = content.replace("document.getElementById('authSubmitBtn').textContent = window.t('auth.register_btn');", "document.getElementById('authSubmitBtn').textContent = 'Create Account';")
        content = content.replace("document.getElementById('authToggleText').textContent = window.t('auth.have_account');", "document.getElementById('authToggleText').textContent = 'Already have an account?';")
        content = content.replace("document.getElementById('authToggleBtn').textContent = window.t('auth.login_here');", "document.getElementById('authToggleBtn').textContent = 'Log In Here';")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Cleaned template:', filepath)

for dirpath, _, filenames in os.walk(templates_dir):
    for f in filenames:
        if f.endswith('.html'):
            clean_template(os.path.join(dirpath, f))
