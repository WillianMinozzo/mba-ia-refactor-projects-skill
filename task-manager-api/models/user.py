import hashlib
import hmac

from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash

from database import commit, db
from models.errors import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError, ValidationError
from models.task import Task
from utils.helpers import is_valid_email, utcnow

DEFAULT_ROLE = 'user'
VALID_ROLES = ('user', 'admin', 'manager')
MIN_PASSWORD_LENGTH = 4
_MODERN_HASH_PREFIXES = ('scrypt:', 'pbkdf2:')


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=DEFAULT_ROLE)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        """Campos públicos apenas: o hash de senha nunca sai do servidor."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at),
        }

    # --- senha

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        if self.password.startswith(_MODERN_HASH_PREFIXES):
            return check_password_hash(self.password, raw_password)
        # Hash MD5 legado (gravado antes da refatoração): verifica e regrava no formato novo.
        legacy_hash = hashlib.md5(raw_password.encode()).hexdigest()
        if hmac.compare_digest(self.password, legacy_hash):
            self.set_password(raw_password)
            return True
        return False

    # --- consultas

    @classmethod
    def get_or_404(cls, user_id):
        user = db.session.get(cls, user_id)
        if user is None:
            raise NotFoundError('Usuário não encontrado')
        return user

    @classmethod
    def find_by_email(cls, email):
        return db.session.scalars(db.select(cls).where(cls.email == email)).first()

    @classmethod
    def list_all(cls):
        return db.session.scalars(db.select(cls).order_by(cls.id)).all()

    @classmethod
    def count_all(cls):
        return db.session.scalar(db.select(func.count(cls.id)))

    @classmethod
    def list_with_task_counts(cls):
        stmt = (
            db.select(cls, func.count(Task.id))
            .outerjoin(Task, Task.user_id == cls.id)
            .group_by(cls.id)
            .order_by(cls.id)
        )
        return [{**user.to_dict(), 'task_count': task_count} for user, task_count in db.session.execute(stmt).all()]

    @classmethod
    def authenticate(cls, email, password):
        user = cls.find_by_email(email)
        if user is None or not isinstance(password, str) or not user.check_password(password):
            raise UnauthorizedError('Credenciais inválidas')
        if not user.active:
            raise ForbiddenError('Usuário inativo')
        commit()  # persiste a regravação de hash legado, se houve
        return user

    # --- escrita

    @classmethod
    def create(cls, data, allow_privileged_role=False):
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', DEFAULT_ROLE)

        if not name:
            raise ValidationError('Nome é obrigatório')
        if not email:
            raise ValidationError('Email é obrigatório')
        if not password:
            raise ValidationError('Senha é obrigatória')
        if not isinstance(name, str):
            raise ValidationError('Nome inválido')
        if not is_valid_email(email):
            raise ValidationError('Email inválido')
        if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
            raise ValidationError('Senha deve ter no mínimo 4 caracteres')
        if cls.find_by_email(email):
            raise ConflictError('Email já cadastrado')
        if role not in VALID_ROLES:
            raise ValidationError('Role inválido')

        user = cls(name=name, email=email, role=role if allow_privileged_role else DEFAULT_ROLE)
        user.set_password(password)
        db.session.add(user)
        commit()
        return user

    def update(self, data, allow_privileged_role=False):
        changes = {}
        if 'name' in data:
            if not isinstance(data['name'], str):
                raise ValidationError('Nome inválido')
            changes['name'] = data['name']
        if 'email' in data:
            if not is_valid_email(data['email']):
                raise ValidationError('Email inválido')
            existing = User.find_by_email(data['email'])
            if existing and existing.id != self.id:
                raise ConflictError('Email já cadastrado')
            changes['email'] = data['email']
        if 'password' in data:
            if not isinstance(data['password'], str) or len(data['password']) < MIN_PASSWORD_LENGTH:
                raise ValidationError('Senha muito curta')
        if 'role' in data:
            if data['role'] not in VALID_ROLES:
                raise ValidationError('Role inválido')
            if allow_privileged_role:
                changes['role'] = data['role']
        if 'active' in data:
            if not isinstance(data['active'], bool):
                raise ValidationError('Campo active inválido')
            changes['active'] = data['active']

        for field, value in changes.items():
            setattr(self, field, value)
        if 'password' in data:
            self.set_password(data['password'])
        commit()
        return self

    def delete_with_tasks(self):
        """Remove o usuário e suas tasks na mesma transação."""
        for task in Task.list_by_user(self.id):
            db.session.delete(task)
        db.session.delete(self)
        commit()
