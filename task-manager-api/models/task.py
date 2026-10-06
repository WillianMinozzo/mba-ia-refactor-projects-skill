from datetime import datetime
from numbers import Real

from sqlalchemy import case, func
from sqlalchemy.orm import joinedload

from database import commit, db
from models.errors import NotFoundError, ValidationError
from utils.helpers import calculate_percentage, utcnow

VALID_STATUSES = ('pending', 'in_progress', 'done', 'cancelled')
CLOSED_STATUSES = ('done', 'cancelled')
DEFAULT_STATUS = 'pending'
MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_PRIORITY = 3
HIGH_PRIORITY_THRESHOLD = 2  # prioridades <= este valor contam como "alta"
MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200
DATE_FORMAT = '%Y-%m-%d'


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=DEFAULT_STATUS)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', backref='tasks')
    category = db.relationship('Category', backref='tasks')

    # --- serialização

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'created_at': str(self.created_at),
            'updated_at': str(self.updated_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'tags': self.tags.split(',') if self.tags else [],
        }

    def to_detail_dict(self):
        return {**self.to_dict(), 'overdue': self.is_overdue()}

    def to_list_dict(self):
        return {
            **self.to_detail_dict(),
            'user_name': self.user.name if self.user else None,
            'category_name': self.category.name if self.category else None,
        }

    def to_summary_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'created_at': str(self.created_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'overdue': self.is_overdue(),
        }

    # --- regras do domínio

    def is_overdue(self, now=None):
        if not self.due_date or self.status in CLOSED_STATUSES:
            return False
        return self.due_date < (now or utcnow())

    # --- consultas

    @classmethod
    def get(cls, task_id):
        return db.session.get(cls, task_id)

    @classmethod
    def get_or_404(cls, task_id):
        task = cls.get(task_id)
        if task is None:
            raise NotFoundError('Task não encontrada')
        return task

    @classmethod
    def list_with_relations(cls):
        stmt = db.select(cls).options(joinedload(cls.user), joinedload(cls.category)).order_by(cls.id)
        return db.session.scalars(stmt).all()

    @classmethod
    def list_by_user(cls, user_id):
        return db.session.scalars(db.select(cls).where(cls.user_id == user_id).order_by(cls.id)).all()

    @classmethod
    def search(cls, text=None, status=None, priority=None, user_id=None):
        stmt = db.select(cls)
        if text:
            stmt = stmt.where(db.or_(cls.title.like(f'%{text}%'), cls.description.like(f'%{text}%')))
        if status:
            stmt = stmt.where(cls.status == status)
        if priority is not None:
            stmt = stmt.where(cls.priority == priority)
        if user_id is not None:
            stmt = stmt.where(cls.user_id == user_id)
        return db.session.scalars(stmt.order_by(cls.id)).all()

    @classmethod
    def _overdue_filter(cls, now):
        open_status = db.or_(cls.status.is_(None), cls.status.not_in(CLOSED_STATUSES))
        return db.and_(cls.due_date.is_not(None), cls.due_date < now, open_status)

    @classmethod
    def list_overdue(cls, now):
        return db.session.scalars(db.select(cls).where(cls._overdue_filter(now)).order_by(cls.id)).all()

    @classmethod
    def count_all(cls):
        return db.session.scalar(db.select(func.count(cls.id)))

    @classmethod
    def count_overdue(cls, now):
        return db.session.scalar(db.select(func.count(cls.id)).where(cls._overdue_filter(now)))

    @classmethod
    def count_by_status(cls):
        counts = dict(db.session.execute(db.select(cls.status, func.count(cls.id)).group_by(cls.status)).all())
        return {status: counts.get(status, 0) for status in VALID_STATUSES}

    @classmethod
    def count_by_priority(cls):
        counts = dict(db.session.execute(db.select(cls.priority, func.count(cls.id)).group_by(cls.priority)).all())
        return {priority: counts.get(priority, 0) for priority in range(MIN_PRIORITY, MAX_PRIORITY + 1)}

    @classmethod
    def count_created_since(cls, since):
        return db.session.scalar(db.select(func.count(cls.id)).where(cls.created_at >= since))

    @classmethod
    def count_done_since(cls, since):
        stmt = db.select(func.count(cls.id)).where(cls.status == 'done', cls.updated_at >= since)
        return db.session.scalar(stmt)

    @classmethod
    def completion_by_user(cls):
        """{user_id: (total, concluídas)} em uma única query."""
        done = func.sum(case((cls.status == 'done', 1), else_=0))
        rows = db.session.execute(db.select(cls.user_id, func.count(cls.id), done).group_by(cls.user_id)).all()
        return {user_id: (total, completed or 0) for user_id, total, completed in rows}

    @classmethod
    def stats(cls):
        total = cls.count_all()
        by_status = cls.count_by_status()
        return {
            'total': total,
            **by_status,
            'overdue': cls.count_overdue(utcnow()),
            'completion_rate': calculate_percentage(by_status['done'], total),
        }

    @classmethod
    def user_statistics(cls, user_id):
        tasks = cls.list_by_user(user_id)
        now = utcnow()
        by_status = {status: 0 for status in VALID_STATUSES}
        for task in tasks:
            if task.status in by_status:
                by_status[task.status] += 1
        total = len(tasks)
        return {
            'total_tasks': total,
            **by_status,
            'overdue': sum(1 for task in tasks if task.is_overdue(now)),
            'high_priority': sum(1 for task in tasks if task.priority <= HIGH_PRIORITY_THRESHOLD),
            'completion_rate': calculate_percentage(by_status['done'], total),
        }

    # --- escrita

    @classmethod
    def create(cls, data):
        task = cls(
            title=_validate_title(data.get('title'), required=True),
            description=data.get('description', ''),
            status=_validate_status(data.get('status', DEFAULT_STATUS)),
            priority=_validate_priority(data.get('priority', DEFAULT_PRIORITY)),
        )
        task.user_id = _validate_user_ref(data.get('user_id'))
        task.category_id = _validate_category_ref(data.get('category_id'))
        due_date = data.get('due_date')
        if due_date:
            task.due_date = _parse_date(due_date, 'Formato de data inválido. Use YYYY-MM-DD')
        tags = data.get('tags')
        if tags:
            task.tags = _join_tags(tags)
        db.session.add(task)
        commit()
        return task

    def update(self, data):
        changes = {}
        if 'title' in data:
            changes['title'] = _validate_title(data['title'], required=False)
        if 'description' in data:
            changes['description'] = data['description']
        if 'status' in data:
            changes['status'] = _validate_status(data['status'])
        if 'priority' in data:
            changes['priority'] = _validate_priority(data['priority'])
        if 'user_id' in data:
            changes['user_id'] = _validate_user_ref(data['user_id'])
        if 'category_id' in data:
            changes['category_id'] = _validate_category_ref(data['category_id'])
        if 'due_date' in data:
            due_date = data['due_date']
            changes['due_date'] = _parse_date(due_date, 'Formato de data inválido') if due_date else None
        if 'tags' in data:
            changes['tags'] = _join_tags(data['tags'])
        for field, value in changes.items():
            setattr(self, field, value)
        self.updated_at = utcnow()
        commit()
        return self

    def delete(self):
        db.session.delete(self)
        commit()


def _validate_title(title, required):
    if required and not title:
        raise ValidationError('Título é obrigatório')
    if not isinstance(title, str):
        raise ValidationError('Título inválido')
    if len(title) < MIN_TITLE_LENGTH:
        raise ValidationError('Título muito curto')
    if len(title) > MAX_TITLE_LENGTH:
        raise ValidationError('Título muito longo')
    return title


def _validate_status(status):
    if not isinstance(status, str) or status not in VALID_STATUSES:
        raise ValidationError('Status inválido')
    return status


def _validate_priority(priority):
    if isinstance(priority, bool) or not isinstance(priority, Real):
        raise ValidationError('Prioridade inválida')
    if priority < MIN_PRIORITY or priority > MAX_PRIORITY:
        raise ValidationError('Prioridade deve ser entre 1 e 5')
    return priority


def _validate_user_ref(user_id):
    from models.user import User

    if user_id and db.session.get(User, user_id) is None:
        raise NotFoundError('Usuário não encontrado')
    return user_id


def _validate_category_ref(category_id):
    from models.category import Category

    if category_id and db.session.get(Category, category_id) is None:
        raise NotFoundError('Categoria não encontrada')
    return category_id


def _parse_date(value, message):
    try:
        return datetime.strptime(value, DATE_FORMAT)
    except (TypeError, ValueError):
        raise ValidationError(message)


def _join_tags(tags):
    if isinstance(tags, list):
        if not all(isinstance(tag, str) for tag in tags):
            raise ValidationError('Tags inválidas')
        return ','.join(tags)
    return tags
