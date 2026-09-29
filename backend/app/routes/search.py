"""
Search Blueprint.
"""

from flask import Blueprint, request, jsonify
from backend.app.extensions import db
from backend.app.models.product import Product
from backend.app.models.search import Search

search_bp = Blueprint('search_bp', __name__)

@search_bp.route('/api/v1/Search', methods=['POST'])
def search():
    data = request.json or {}
    user_id = data.get('user_id')
    keyword = data.get('keyword') or data.get('query')
    
    if not user_id or not keyword:
        return jsonify({'error': 'Invalid request data'}), 400

    try:
        search_record = Search(user_id=user_id, query=keyword)
        db.session.add(search_record)
        db.session.commit()
        
        products = Product.query.filter(
            Product.moderation_status == 'approved',
            Product.name.ilike(f'%{keyword}%')
        ).all()
        product_list = [p.to_dict() for p in products]

        return jsonify({
            'status': 'success',
            'data': product_list
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
