"""Dados de exemplo. Apaga o conteúdo atual e recria tudo em uma única transação."""
from datetime import timedelta

from database.connection import commit, db
from models.category import Category
from models.task import Task
from models.user import User
from utils.helpers import utcnow

USERS = [
    {'name': 'João Silva', 'email': 'joao@email.com', 'password': '1234', 'role': 'admin'},
    {'name': 'Maria Santos', 'email': 'maria@email.com', 'password': 'abcd', 'role': 'user'},
    {'name': 'Pedro Oliveira', 'email': 'pedro@email.com', 'password': 'pass', 'role': 'manager'},
]

CATEGORIES = [
    {'name': 'Backend', 'description': 'Tarefas de backend', 'color': '#3498db'},
    {'name': 'Frontend', 'description': 'Tarefas de frontend', 'color': '#2ecc71'},
    {'name': 'DevOps', 'description': 'Tarefas de infraestrutura', 'color': '#e74c3c'},
    {'name': 'Bug', 'description': 'Correção de bugs', 'color': '#e67e22'},
]

# user/category são índices nas listas acima; due_in_days é relativo a hoje.
TASKS = [
    {'title': 'Implementar autenticação JWT', 'description': 'Adicionar autenticação real com JWT', 'status': 'pending', 'priority': 1, 'user': 0, 'category': 0, 'due_in_days': -3},
    {'title': 'Criar tela de login', 'description': 'Tela de login responsiva', 'status': 'in_progress', 'priority': 2, 'user': 1, 'category': 1, 'due_in_days': 5},
    {'title': 'Configurar CI/CD', 'description': 'Pipeline com GitHub Actions', 'status': 'done', 'priority': 2, 'user': 2, 'category': 2, 'tags': 'devops,ci,github'},
    {'title': 'Corrigir bug no filtro de busca', 'description': 'Filtro não funciona com caracteres especiais', 'status': 'pending', 'priority': 1, 'user': 0, 'category': 3, 'due_in_days': -1},
    {'title': 'Adicionar paginação na API', 'description': 'Endpoints retornam todos os registros', 'status': 'pending', 'priority': 3, 'user': 0, 'category': 0, 'due_in_days': 10},
    {'title': 'Escrever testes unitários', 'description': 'Cobertura mínima de 80%', 'status': 'pending', 'priority': 2, 'user': 1, 'category': 0},
    {'title': 'Documentar API com Swagger', 'description': 'Gerar documentação automática', 'status': 'cancelled', 'priority': 4, 'user': 2, 'category': 0},
    {'title': 'Refatorar models', 'description': 'Melhorar organização dos models', 'status': 'in_progress', 'priority': 3, 'user': 1, 'category': 0, 'tags': 'refactor,tech-debt'},
    {'title': 'Configurar monitoramento', 'description': 'Prometheus + Grafana', 'status': 'pending', 'priority': 4, 'user': 2, 'category': 2, 'due_in_days': 20},
    {'title': 'Melhorar validações de input', 'description': 'Usar marshmallow ou pydantic', 'status': 'pending', 'priority': 3, 'user': 0, 'category': 0, 'tags': 'improvement,validation'},
]


def seed_data():
    """Deve rodar dentro de um app context. Devolve as contagens finais."""
    db.session.execute(db.delete(Task))
    db.session.execute(db.delete(User))
    db.session.execute(db.delete(Category))

    users = []
    for spec in USERS:
        user = User(name=spec['name'], email=spec['email'], role=spec['role'])
        user.set_password(spec['password'])
        users.append(user)
    categories = [Category(**spec) for spec in CATEGORIES]
    db.session.add_all(users + categories)
    db.session.flush()

    now = utcnow()
    for spec in TASKS:
        task = Task(
            title=spec['title'],
            description=spec['description'],
            status=spec['status'],
            priority=spec['priority'],
            user_id=users[spec['user']].id,
            category_id=categories[spec['category']].id,
            tags=spec.get('tags'),
        )
        if 'due_in_days' in spec:
            task.due_date = now + timedelta(days=spec['due_in_days'])
        db.session.add(task)
    commit()

    return {'users': User.count_all(), 'categories': Category.count_all(), 'tasks': Task.count_all()}
