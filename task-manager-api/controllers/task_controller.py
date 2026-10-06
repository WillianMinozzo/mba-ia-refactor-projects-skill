import logging

from flask import jsonify, request

from controllers.helpers import int_query_arg, json_body
from models.task import Task

logger = logging.getLogger(__name__)


def list_tasks():
    return jsonify([task.to_list_dict() for task in Task.list_with_relations()]), 200


def get_task(task_id):
    return jsonify(Task.get_or_404(task_id).to_detail_dict()), 200


def create_task():
    task = Task.create(json_body())
    logger.info('Task criada: id=%s', task.id)
    return jsonify(task.to_dict()), 201


def update_task(task_id):
    task = Task.get_or_404(task_id)
    task.update(json_body())
    logger.info('Task atualizada: id=%s', task.id)
    return jsonify(task.to_dict()), 200


def delete_task(task_id):
    Task.get_or_404(task_id).delete()
    logger.info('Task deletada: id=%s', task_id)
    return jsonify({'message': 'Task deletada com sucesso'}), 200


def search_tasks():
    tasks = Task.search(
        text=request.args.get('q', ''),
        status=request.args.get('status', ''),
        priority=int_query_arg('priority', 'Prioridade inválida'),
        user_id=int_query_arg('user_id', 'Usuário inválido'),
    )
    return jsonify([task.to_dict() for task in tasks]), 200


def task_stats():
    return jsonify(Task.stats()), 200
