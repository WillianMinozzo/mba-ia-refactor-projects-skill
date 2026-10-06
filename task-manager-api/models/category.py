from sqlalchemy import func

from database import commit, db
from models.errors import NotFoundError, ValidationError
from models.task import Task
from utils.helpers import utcnow

DEFAULT_COLOR = '#000000'


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    color = db.Column(db.String(7), default=DEFAULT_COLOR)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'created_at': str(self.created_at),
        }

    @classmethod
    def get_or_404(cls, category_id):
        category = db.session.get(cls, category_id)
        if category is None:
            raise NotFoundError('Categoria não encontrada')
        return category

    @classmethod
    def count_all(cls):
        return db.session.scalar(db.select(func.count(cls.id)))

    @classmethod
    def list_with_task_counts(cls):
        stmt = (
            db.select(cls, func.count(Task.id))
            .outerjoin(Task, Task.category_id == cls.id)
            .group_by(cls.id)
            .order_by(cls.id)
        )
        return [{**category.to_dict(), 'task_count': count} for category, count in db.session.execute(stmt).all()]

    @classmethod
    def create(cls, data):
        name = data.get('name')
        if not name:
            raise ValidationError('Nome é obrigatório')
        if not isinstance(name, str):
            raise ValidationError('Nome inválido')
        category = cls(name=name, description=data.get('description', ''), color=data.get('color', DEFAULT_COLOR))
        db.session.add(category)
        commit()
        return category

    def update(self, data):
        for field in ('name', 'description', 'color'):
            if field in data:
                setattr(self, field, data[field])
        commit()
        return self

    def delete(self):
        db.session.delete(self)
        commit()
