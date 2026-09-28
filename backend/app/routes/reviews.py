"""
Reviews Blueprint.
"""

from flask import Blueprint, request, jsonify
from backend.app.extensions import db
from backend.app.models.reviews import Reviews

reviews_bp = Blueprint('reviews_bp', __name__)

@reviews_bp.route('/api/v1/Reviews', methods=['GET'])
def view_all_reviews():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))

    reviews_page = Reviews.query.paginate(page=page, per_page=per_page, error_out=False)
    review_list = [r.to_dict() for r in reviews_page.items]

    return jsonify({
        'status': 'success',
        'data': review_list,
        'pages': reviews_page.pages
    })

@reviews_bp.route('/api/v1/Reviews/create', methods=['POST'])
def create_review():
    data = request.json or {}

    review = Reviews(
        product_id=data['product_id'],
        user_id=data['user_id'],
        comment=data['comment'],                      
        rating=data['rating']                     
    )
    db.session.add(review)
    db.session.commit()
    return jsonify({'message': 'Reviews have been greatly appreciated'}), 201
