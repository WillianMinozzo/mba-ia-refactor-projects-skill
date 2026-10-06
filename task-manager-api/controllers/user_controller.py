import logging

from flask import current_app, jsonify

from controllers.helpers import json_body
from middlewares.auth import is_admin_request
from models.errors import ValidationError
from models.task import Task
from models.user import User
from services.auth_service import issue_token

logger = logging.getLogger(__name__)


def list_users():
    return jsonify(User.list_with_task_counts()), 200


def get_user(user_id):
    user = User.get_or_404(user_id)
    return jsonify({**user.to_dict(), 'tasks': [task.to_dict() for task in Task.list_by_user(user_id)]}), 200


def create_user():
    user = User.create(json_body(), allow_privileged_role=is_admin_request())
    logger.info('Usuário criado: id=%s', user.id)
    return jsonify(user.to_dict()), 201


def update_user(user_id):
    user = User.get_or_404(user_id)
    user.update(json_body(), allow_privileged_role=is_admin_request())
    return jsonify(user.to_dict()), 200


def delete_user(user_id):
    User.get_or_404(user_id).delete_with_tasks()
    logger.info('Usuário deletado: id=%s', user_id)
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200


def get_user_tasks(user_id):
    User.get_or_404(user_id)
    return jsonify([task.to_summary_dict() for task in Task.list_by_user(user_id)]), 200


def login():
    data = json_body()
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        raise ValidationError('Email e senha são obrigatórios')
    user = User.authenticate(email, password)
    return jsonify({
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': issue_token(user, current_app.config['SECRET_KEY']),
    }), 200
