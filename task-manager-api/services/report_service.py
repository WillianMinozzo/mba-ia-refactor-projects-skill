"""Relatórios que agregam dados de Task, User e Category."""
from datetime import timedelta

from models.category import Category
from models.task import Task
from models.user import User
from utils.helpers import calculate_percentage, utcnow

RECENT_ACTIVITY_DAYS = 7
PRIORITY_LABELS = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}


def build_summary():
    now = utcnow()
    since = now - timedelta(days=RECENT_ACTIVITY_DAYS)
    by_priority = Task.count_by_priority()
    overdue_tasks = Task.list_overdue(now)
    completion = Task.completion_by_user()

    return {
        'generated_at': str(now),
        'overview': {
            'total_tasks': Task.count_all(),
            'total_users': User.count_all(),
            'total_categories': Category.count_all(),
        },
        'tasks_by_status': Task.count_by_status(),
        'tasks_by_priority': {label: by_priority[priority] for priority, label in PRIORITY_LABELS.items()},
        'overdue': {
            'count': len(overdue_tasks),
            'tasks': [
                {
                    'id': task.id,
                    'title': task.title,
                    'due_date': str(task.due_date),
                    'days_overdue': (now - task.due_date).days,
                }
                for task in overdue_tasks
            ],
        },
        'recent_activity': {
            'tasks_created_last_7_days': Task.count_created_since(since),
            'tasks_completed_last_7_days': Task.count_done_since(since),
        },
        'user_productivity': [_user_productivity(user, *completion.get(user.id, (0, 0))) for user in User.list_all()],
    }


def build_user_report(user_id):
    user = User.get_or_404(user_id)
    return {
        'user': {'id': user.id, 'name': user.name, 'email': user.email},
        'statistics': Task.user_statistics(user_id),
    }


def _user_productivity(user, total, completed):
    return {
        'user_id': user.id,
        'user_name': user.name,
        'total_tasks': total,
        'completed_tasks': completed,
        'completion_rate': calculate_percentage(completed, total),
    }
