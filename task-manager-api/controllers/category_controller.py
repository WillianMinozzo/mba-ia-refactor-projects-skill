from flask import jsonify

from controllers.helpers import json_body
from models.category import Category


def list_categories():
    return jsonify(Category.list_with_task_counts()), 200


def create_category():
    return jsonify(Category.create(json_body()).to_dict()), 201


def update_category(cat_id):
    category = Category.get_or_404(cat_id)
    return jsonify(category.update(json_body(allow_empty=True)).to_dict()), 200


def delete_category(cat_id):
    Category.get_or_404(cat_id).delete()
    return jsonify({'message': 'Categoria deletada'}), 200
