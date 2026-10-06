# Playbook de Refatoração

Guia da Fase 3. Uma transformação (`T-xx`) para cada anti-pattern do catálogo, com antes/depois. Os exemplos estão em Python e JavaScript para ilustrar; aplique o mesmo movimento com os recursos idiomáticos do stack detectado.

Princípios válidos para todas:

- **Mover antes de melhorar.** Primeiro leve o código para a camada certa preservando o comportamento; depois corrija o problema dentro dela.
- **Uma transformação por vez**, verificando que o projeto ainda importa/compila.
- **Comportamento observável igual**: mesmos status e mesmas chaves de resposta, salvo as mudanças intencionais de contrato das guidelines.
- **Preferir o que já existe**: biblioteca padrão, dependências instaladas, helpers e métodos que o próprio projeto já tem.

| ID | Transformação | Resolve |
|---|---|---|
| T-01 | Extrair configuração para módulo que lê o ambiente | AP-01, AP-10, AP-17 |
| T-02 | Parametrizar queries e fechar execução arbitrária | AP-02 |
| T-03 | Hash de senha seguro com migração transparente | AP-03 |
| T-04 | Serialização sem dados sensíveis | AP-04 |
| T-05 | Decompor God Class/Module por domínio e camada | AP-05 |
| T-06 | Guarda de acesso em rotas administrativas | AP-06 |
| T-07 | Controller fino: mover regra para model/service | AP-07 |
| T-08 | Completar, usar ou remover camadas | AP-08 |
| T-09 | Eliminar estado global; injetar dependências | AP-09, AP-17 |
| T-10 | Envolver escritas dependentes em transação | AP-11 |
| T-11 | Eliminar N+1 com JOIN, carga antecipada ou agregação | AP-12 |
| T-12 | Centralizar validação de entrada | AP-13 |
| T-13 | Tratamento de erro centralizado | AP-14, AP-19 |
| T-14 | Substituir APIs deprecated | AP-15 |
| T-15 | Remover duplicação | AP-16 |
| T-16 | Achatar callbacks com async/await | AP-18 |
| T-17 | Higiene: constantes, nomes, logger, código morto | AP-20 a AP-23 |

---

## T-01 — Extrair configuração para módulo que lê o ambiente

Antes:

```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
app.run(host="0.0.0.0", port=5000, debug=True)
```

Depois:

```python
# config/settings.py
import os, secrets, logging

def _bool(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes")

def _secret(name):
    value = os.getenv(name)
    if value:
        return value
    if os.getenv("APP_ENV", "development") == "production":
        raise RuntimeError(f"{name} must be set in production")
    logging.getLogger(__name__).warning("%s not set; using an ephemeral value", name)
    return secrets.token_hex(32)

class Settings:
    SECRET_KEY = _secret("SECRET_KEY")
    DEBUG = _bool("DEBUG", False)
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "5000"))
    DATABASE_PATH = os.getenv("DATABASE_PATH", "loja.db")
```

```javascript
// src/config/index.js
const crypto = require('crypto');
const env = process.env;

function secret(name) {
  if (env[name]) return env[name];
  if (env.NODE_ENV === 'production') throw new Error(`${name} must be set in production`);
  console.warn(`[config] ${name} not set; using an ephemeral value`);
  return crypto.randomBytes(32).toString('hex');
}

module.exports = Object.freeze({
  port: Number(env.PORT) || 3000,
  dbFile: env.DB_FILE || ':memory:',
  paymentGatewayKey: secret('PAYMENT_GATEWAY_KEY'),
});
```

Passos:
1. Liste todo literal de configuração (segredos, URIs, debug, host, porta, credenciais de serviços externos).
2. Crie o módulo de config com padrão igual ao valor original para o que **não** é segredo.
3. Segredos nunca têm padrão literal: valor efêmero fora de produção, erro em produção.
4. Crie `.env.example` listando cada variável com valor fictício; garanta `.env` no `.gitignore`.
5. Só use biblioteca de `.env` se ela já for dependência do projeto.
6. Apague os literais originais — inclusive cópias em outros arquivos (endpoints de health, logs).

## T-02 — Parametrizar queries e fechar execução arbitrária

Antes:

```python
cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'")
query += " AND nome LIKE '%" + termo + "%'"
```

Depois:

```python
cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))

clauses, params = ["1=1"], []
if termo:
    clauses.append("(nome LIKE ? OR descricao LIKE ?)")
    params += [f"%{termo}%", f"%{termo}%"]
cursor.execute("SELECT * FROM produtos WHERE " + " AND ".join(clauses), params)
```

```javascript
// antes
db.all(`SELECT * FROM users WHERE email = '${email}'`, cb);
// depois
db.all('SELECT * FROM users WHERE email = ?', [email], cb);
```

Passos:
1. Todo valor externo vira parâmetro; a string de SQL só contém literais e placeholders do driver (`?`, `%s`, `$1`, `:nome`).
2. Filtros dinâmicos: monte lista de cláusulas fixas + lista de parâmetros.
3. Identificadores dinâmicos (coluna, ordenação) passam por lista de valores permitidos; nunca são parametrizáveis.
4. Endpoint que executa SQL/comando recebido do cliente: não há parametrização possível. Aplique T-06 (guarda, desabilitado sem credencial configurada) e mantenha a rota registrada.

## T-03 — Hash de senha seguro com migração transparente

Antes:

```python
self.password = hashlib.md5(pwd.encode()).hexdigest()
```

Depois:

```python
from werkzeug.security import generate_password_hash, check_password_hash

def set_password(self, raw):
    self.password = generate_password_hash(raw)

def check_password(self, raw):
    if self.password.startswith(("scrypt:", "pbkdf2:")):
        return check_password_hash(self.password, raw)
    legacy_ok = hmac.compare_digest(self.password, hashlib.md5(raw.encode()).hexdigest())
    if legacy_ok:
        self.set_password(raw)   # regrava no formato novo; quem chama persiste
    return legacy_ok
```

```javascript
const crypto = require('crypto');

function hashPassword(raw) {
  const salt = crypto.randomBytes(16).toString('hex');
  return `scrypt$${salt}$${crypto.scryptSync(raw, salt, 64).toString('hex')}`;
}

function verifyPassword(raw, stored) {
  const [scheme, salt, hash] = String(stored).split('$');
  if (scheme !== 'scrypt') return false;
  const candidate = crypto.scryptSync(raw, salt, 64);
  return crypto.timingSafeEqual(candidate, Buffer.from(hash, 'hex'));
}
```

Passos:
1. Use o helper de senha do framework ou KDF da biblioteca padrão (`scrypt`, `PBKDF2`); adicionar `bcrypt`/`argon2` só se já for dependência.
2. Login passa a buscar o usuário pelo identificador e verificar o hash em código — nunca `WHERE senha = ?`.
3. Se pode haver dados gravados no formato antigo, verifique o formato legado e regrave no novo após login bem-sucedido.
4. Atualize os seeds para gravar hash.
5. Remova senha padrão: sem senha informada, a requisição é inválida — exceto se isso alterar um fluxo existente que os clientes usam; nesse caso gere senha aleatória e registre como recomendação.

## T-04 — Serialização sem dados sensíveis

Antes:

```python
def to_dict(self):
    return {"id": self.id, "email": self.email, "password": self.password, "role": self.role}
```

Depois:

```python
PUBLIC_FIELDS = ("id", "name", "email", "role", "active", "created_at")

def to_dict(self):
    return {field: getattr(self, field) for field in self.PUBLIC_FIELDS}
```

Passos:
1. Defina por entidade a lista explícita de campos públicos; serialize por inclusão, nunca por exclusão.
2. Troque `SELECT *` devolvido ao cliente por colunas nomeadas ou passe pelo serializador.
3. Endpoints de health/diagnóstico devolvem só status; remova chaves, caminhos e flags internas.
4. Tire de logs: senhas, tokens, números de cartão (no máximo os 4 últimos dígitos), chaves.
5. Respostas 500 levam mensagem genérica; o detalhe vai para o log (T-13).
6. Registre cada campo removido como mudança intencional de contrato.

## T-05 — Decompor God Class/Module por domínio e camada

Antes — uma classe faz tudo:

```javascript
class AppManager {
  constructor() { this.db = new sqlite3.Database(':memory:'); }
  initDb() { /* CREATE TABLE ... INSERT ... */ }
  setupRoutes(app) {
    app.post('/api/checkout', (req, res) => { /* validação + SQL + pagamento + auditoria */ });
    app.get('/api/admin/financial-report', (req, res) => { /* SQL aninhado */ });
  }
}
```

Depois — uma responsabilidade por unidade:

```
database/connection.js   abre a conexão
database/schema.js       CREATE TABLE
database/seed.js         dados iniciais
models/userModel.js      findByEmail, create, remove
models/courseModel.js    findActiveById, findAll
models/enrollmentModel.js / paymentModel.js / auditLogModel.js
services/checkoutService.js   fluxo de checkout (vários models, transação)
controllers/checkoutController.js / reportController.js / userController.js
routes/index.js          registra os Routers
app.js                   composition root
```

Passos:
1. Inventarie as responsabilidades da unidade: conexão, schema, seed, cada entidade, cada fluxo, registro de rotas.
2. Extraia nesta ordem: infraestrutura de dados → um model por entidade → services para fluxos com vários models → controllers → routes.
3. Em arquivo-camada único (`models.py` com todos os domínios), divida por entidade mantendo as assinaturas, e atualize os imports.
4. Apague a unidade original quando nada mais a importar. Não deixe "casca" reexportando tudo.

## T-06 — Guarda de acesso em rotas administrativas

Duas políticas, conforme a classe da rota no inventário. A regra que não pode ser violada: **com o boot padrão, toda rota não `destructive` continua respondendo como antes.**

| Rota | Sem credencial configurada | Com credencial configurada |
|---|---|---|
| `destructive` (apaga em massa, reseta banco, executa SQL/comando arbitrário) | **403** — desabilitada | 401 sem o header; comportamento original com ele |
| Administrativa não destrutiva (prefixo admin, relatório com dados de todos, exclusão de um recurso alheio) | Fora de produção: **responde como antes**, com aviso no log de boot. Em produção: 403 | 401 sem o header; comportamento original com ele |

Antes:

```python
@app.route("/admin/reset-db", methods=["POST"])
def reset_database():
    cursor.execute("DELETE FROM pedidos")
```

Depois:

```python
# middlewares/auth.py
from functools import wraps
from hmac import compare_digest
from flask import request, jsonify, current_app

def _guard(view, strict):
    @wraps(view)
    def wrapper(*args, **kwargs):
        expected = current_app.config.get("ADMIN_TOKEN")
        if not expected:
            open_by_default = not strict and current_app.config.get("APP_ENV") != "production"
            if open_by_default:
                return view(*args, **kwargs)
            return jsonify({"erro": "Rota administrativa desabilitada"}), 403
        if not compare_digest(request.headers.get("X-Admin-Token", ""), expected):
            return jsonify({"erro": "Não autorizado"}), 401
        return view(*args, **kwargs)
    return wrapper

def require_admin(view):          # rotas destructive: fechadas sem token
    return _guard(view, strict=True)

def admin_when_configured(view):  # demais rotas administrativas: exigem token só se configurado
    return _guard(view, strict=False)
```

```javascript
// middlewares/auth.js
const crypto = require('crypto');

function adminGuard(config, { strict }) {
  return (req, res, next) => {
    if (!config.adminToken) {
      const openByDefault = !strict && config.env !== 'production';
      return openByDefault ? next() : res.status(403).send('Rota administrativa desabilitada');
    }
    const provided = Buffer.from(String(req.get('x-admin-token') || ''));
    const expected = Buffer.from(config.adminToken);
    const ok = provided.length === expected.length && crypto.timingSafeEqual(provided, expected);
    return ok ? next() : res.status(401).send('Não autorizado');
  };
}
```

Passos:
1. Classifique cada rota sensível: `destructive` recebe a guarda estrita; as demais administrativas recebem a guarda condicional. Rotas comuns do negócio não recebem guarda (autenticação geral fica adiada).
2. A credencial vem da config (`ADMIN_TOKEN`), sem valor padrão no código. Sem ela, registre um aviso no boot dizendo quais rotas estão abertas e quais estão desabilitadas.
3. Privilégio autoatribuído: no cadastro público, ignore `role`/`tipo` vindo do cliente e use o padrão.
4. Token falso/previsível: substitua por token aleatório (`secrets.token_urlsafe`, `crypto.randomBytes`) mantendo a mesma chave na resposta. Implementar verificação de token em todas as rotas fica adiado.
5. Use o formato de erro que a aplicação já adota (JSON com a mesma chave, ou texto, se era texto).
6. Não altere arquivos de exemplo de requisição para exigir o header nas rotas que continuam abertas por padrão; documente o header como opcional.
7. No resumo final, o finding de controle de acesso é `resolved` para as rotas `destructive` e para o privilégio autoatribuído, e declara explicitamente que as demais rotas administrativas ficam protegidas **quando `ADMIN_TOKEN` é definido**.

## T-07 — Controller fino: mover regra para model/service

Antes:

```python
@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = Task.query.all()
    result = []
    for t in tasks:
        data = {'id': t.id, 'title': t.title}
        if t.due_date and t.due_date < datetime.utcnow() and t.status not in ('done', 'cancelled'):
            data['overdue'] = True
        user = User.query.get(t.user_id)
        data['user_name'] = user.name if user else None
        result.append(data)
    return jsonify(result), 200
```

Depois:

```python
# models/task.py
class Task(db.Model):
    @classmethod
    def list_with_relations(cls):
        stmt = db.select(cls).options(joinedload(cls.user), joinedload(cls.category))
        return db.session.scalars(stmt).all()

    def to_detail_dict(self):
        return {**self.to_dict(), 'overdue': self.is_overdue(),
                'user_name': self.user.name if self.user else None}

# controllers/task_controller.py
def list_tasks():
    return jsonify([t.to_detail_dict() for t in Task.list_with_relations()]), 200

# routes/task_routes.py
task_bp.add_url_rule('/tasks', view_func=task_controller.list_tasks, methods=['GET'])
```

Passos:
1. Para cada handler, separe: (a) leitura da entrada, (b) validação, (c) regra/consulta, (d) efeitos colaterais, (e) montagem da resposta.
2. (c) vai para o model; se envolve vários models, para um service. (d) vai para um service. (b) segue T-12.
3. O controller fica com (a), a chamada e (e).
4. Efeito colateral simulado por `print` vira chamada a um service de notificação (existente no projeto, se houver) com logger.

## T-08 — Completar, usar ou remover camadas

Antes — a camada existe mas não é usada:

```python
# utils/helpers.py — ninguém importa
def process_task_data(data, existing_task=None): ...
VALID_STATUSES = ['pending', 'in_progress', 'done', 'cancelled']

# routes/task_routes.py — duplica inline
if status not in ['pending', 'in_progress', 'done', 'cancelled']:
    return jsonify({'error': 'Status inválido'}), 400
```

Depois:

```python
# controllers/task_controller.py
from utils.helpers import process_task_data

def create_task():
    payload, error = process_task_data(request.get_json(silent=True) or {})
    if error:
        raise ValidationError(error)
    return jsonify(Task.create(**payload).to_dict()), 201
```

Passos:
1. **Camada ausente**: crie-a (em N2, tipicamente `controllers/` e `config/`) e mova para ela o que hoje está nas rotas.
2. **Camada morta**: se o código é correto e cobre o que está duplicado inline, passe a usá-lo e apague as cópias. Se é redundante ou quebrado, remova-o. Confirme que mensagens e status permanecem os mesmos ao adotar o helper; ajuste o helper se divergirem.
3. **Responsabilidade trocada**: mova o recurso para um módulo com o nome dele (rotas + controller próprios), mantendo os caminhos HTTP.
4. **Dependência invertida**: remova o import da camada superior; passe o dado por parâmetro.

## T-09 — Eliminar estado global; injetar dependências

Antes:

```python
db_connection = None

def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect("loja.db", check_same_thread=False)
        # CREATE TABLE ... INSERT seeds ...
    return db_connection
```

Depois:

```python
# database/connection.py
import sqlite3
from flask import current_app, g

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

# app.py
def create_app(settings=Settings):
    app = Flask(__name__)
    app.config.from_object(settings)
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_schema(); seed_if_empty()
    register_routes(app); register_error_handlers(app)
    return app
```

```javascript
// app.js — composition root
const db = createConnection(config);
const models = createModels(db);                 // cada model recebe db
const services = createServices(models, config);
app.use('/api', createRoutes(createControllers(models, services), config));
```

Passos:
1. Recurso compartilhado (conexão, cache, cliente externo) é criado no composition root e entregue por parâmetro, factory ou contexto de requisição do framework.
2. Schema e seed saem da função de conexão para funções próprias, chamadas explicitamente no boot. O seed só insere se a tabela estiver vazia, como antes.
3. Cache em memória: defina limite/expiração ou remova se ninguém lê.
4. Acumulador de negócio em variável de módulo: calcule a partir do banco ou remova se não é lido.

## T-10 — Envolver escritas dependentes em transação

Antes:

```python
cursor.execute("INSERT INTO pedidos ...")
for item in itens:
    cursor.execute("INSERT INTO itens_pedido ...")
    cursor.execute("UPDATE produtos SET estoque = estoque - ? ...")
db.commit()
```

Depois:

```python
try:
    cursor.execute("INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)", (usuario_id, total))
    for item in itens:
        cursor.execute("INSERT INTO itens_pedido ...", (...))
        cursor.execute("UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?", (qtd, pid, qtd))
        if cursor.rowcount == 0:
            raise BusinessRuleError("Estoque insuficiente")
    db.commit()
except Exception:
    db.rollback()
    raise
```

```javascript
await db.run('BEGIN');
try {
  const enrollment = await enrollmentModel.create(userId, courseId);
  await paymentModel.create(enrollment.id, course.price, status);
  await db.run('COMMIT');
} catch (err) {
  await db.run('ROLLBACK');
  throw err;
}
```

Passos:
1. Faça todas as validações antes da primeira escrita.
2. Uma unidade de trabalho por operação de negócio: commit no fim, rollback em qualquer erro.
3. Exclusão de registro pai: remova ou trate os filhos na mesma transação, na ordem das dependências.
4. Leitura seguida de escrita condicional: mova a condição para o `WHERE` do `UPDATE` e confira linhas afetadas.

## T-11 — Eliminar N+1

Antes:

```python
for row in pedidos:
    cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
    for item in cursor2.fetchall():
        cursor3.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
```

Depois:

```python
cursor.execute("""
    SELECT i.pedido_id, i.produto_id, i.quantidade, i.preco_unitario, p.nome AS produto_nome
    FROM itens_pedido i LEFT JOIN produtos p ON p.id = i.produto_id
    WHERE i.pedido_id IN ({})""".format(",".join("?" * len(ids))), ids)
itens_por_pedido = defaultdict(list)
for row in cursor.fetchall():
    itens_por_pedido[row["pedido_id"]].append(dict(row))
```

Com ORM:

```python
# antes: len(u.tasks) dentro do laço; Task.query.filter_by(category_id=c.id).count() por categoria
counts = dict(db.session.execute(
    db.select(Task.category_id, db.func.count()).group_by(Task.category_id)).all())
```

Passos:
1. Uma query traz os pais; **uma** query traz todos os filhos (JOIN ou `IN`); o agrupamento é feito em memória.
2. Com ORM: carga antecipada (`joinedload`/`selectinload`, `include`, `with`) no lugar de acesso lazy em laço.
3. Contagens por item: `GROUP BY` único. Vários `COUNT` com filtros diferentes: uma query com agregação condicional ou `GROUP BY`.
4. A lista de `IN` vazia precisa ser tratada (não execute a query).
5. Mantenha a ordem e o formato do resultado original.

## T-12 — Centralizar validação de entrada

Antes:

```python
if not dados: return jsonify({"erro": "Dados inválidos"}), 400
if "nome" not in dados: return jsonify({"erro": "Nome é obrigatório"}), 400
if preco < 0: return jsonify({"erro": "Preço não pode ser negativo"}), 400
# ... repetido em atualizar_produto
```

Depois:

```python
# validators/produto_validator.py
def validar_produto(dados):
    if not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")
    for campo, rotulo in (("nome", "Nome"), ("preco", "Preço"), ("estoque", "Estoque")):
        if campo not in dados:
            raise ValidationError(f"{rotulo} é obrigatório")
    if not isinstance(dados["preco"], (int, float)) or dados["preco"] < 0:
        raise ValidationError("Preço não pode ser negativo")
    return {"nome": dados["nome"].strip(), "preco": dados["preco"], ...}
```

Passos:
1. Uma função de validação por recurso, usada por criar e atualizar (com parâmetro para campos parciais quando o original permitia).
2. Preserve mensagens e status originais; acrescente apenas checagens que faltavam (corpo ausente, tipo errado), respondendo 400.
3. O validador lança erro de validação; a conversão para resposta é do handler central (T-13).
4. Use biblioteca de schema apenas se já for usada no projeto.

## T-13 — Tratamento de erro centralizado

Antes:

```python
def listar_produtos():
    try:
        return jsonify({"dados": models.get_todos_produtos(), "sucesso": True}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
```

Depois:

```python
# middlewares/error_handler.py
class AppError(Exception):
    status = 400
class ValidationError(AppError): status = 400
class NotFoundError(AppError): status = 404

def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({"erro": str(err), "sucesso": False}), err.status

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        if isinstance(err, HTTPException):
            return err
        app.logger.exception("Unhandled error")
        return jsonify({"erro": "Erro interno do servidor"}), 500

# controller
def listar_produtos():
    return jsonify({"dados": produto_model.listar(), "sucesso": True}), 200
```

```javascript
// middlewares/errorHandler.js
class AppError extends Error {
  constructor(status, message) { super(message); this.status = status; }
}
const asyncHandler = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);

function errorHandler(err, req, res, next) {
  if (err instanceof AppError) return res.status(err.status).send(err.message);
  console.error(err);
  return res.status(500).send('Internal server error');
}
```

Passos:
1. Defina poucas exceções de domínio com status associado.
2. Registre um handler central por último na cadeia. Erros HTTP do próprio framework (404 de rota, 405) passam sem alteração.
3. Remova os `try/except` genéricos dos controllers; `except:` sem tipo vira o tipo específico ou some.
4. O corpo de erro mantém o formato e a chave que cada rota já usava (JSON com a mesma chave, ou texto, se era texto).
5. Em frameworks que não propagam rejeição assíncrona, envolva os handlers (`asyncHandler`).
6. Callback com erro ignorado: trate ou propague sempre.

## T-14 — Substituir APIs deprecated

Antes:

```python
created_at = db.Column(db.DateTime, default=datetime.utcnow)
task = Task.query.get(task_id)
```

Depois:

```python
def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)   # mantém datetime ingênuo como o schema atual

created_at = db.Column(db.DateTime, default=utcnow)
task = db.session.get(Task, task_id)
```

```javascript
// antes
const buf = new Buffer(text); const q = url.parse(req.url, true).query;
// depois
const buf = Buffer.from(text); const q = Object.fromEntries(new URL(req.url, base).searchParams);
```

Passos:
1. Use o equivalente indicado no catálogo para a versão declarada no manifesto.
2. Preserve a semântica: se o código compara datas ingênuas gravadas no banco, o substituto continua devolvendo data ingênua em UTC; não misture datas com e sem fuso.
3. Centralize o substituto em um helper quando a chamada se repete.
4. Rode a busca de novo ao final; nenhuma ocorrência deve restar.

## T-15 — Remover duplicação

Antes:

```python
def get_todos_produtos():
    return [{"id": r["id"], "nome": r["nome"], "preco": r["preco"]} for r in rows]
def get_produto_por_id(id):
    return {"id": row["id"], "nome": row["nome"], "preco": row["preco"]}
```

Depois:

```python
def _to_dict(row):
    return {campo: row[campo] for campo in CAMPOS_PUBLICOS}

def listar():
    return [_to_dict(r) for r in rows]
def buscar_por_id(produto_id):
    return _to_dict(row) if row else None
```

Passos:
1. Se já existe implementação canônica (método do model, helper), use-a e apague as cópias.
2. Senão, extraia uma função na camada dona do conceito: regra de negócio no model, formatação no serializador, validação no validador.
3. Funções que diferem só por um filtro viram uma função com parâmetro.
4. Verifique que cada cópia tinha o mesmo comportamento; se alguma divergia, preserve o comportamento observável de cada rota.

## T-16 — Achatar callbacks com async/await

Antes:

```javascript
db.get('SELECT * FROM courses WHERE id = ?', [cid], (err, course) => {
  db.get('SELECT id FROM users WHERE email = ?', [email], (err, user) => {
    db.run('INSERT INTO enrollments ...', [user.id, cid], function (err) {
      db.run('INSERT INTO payments ...', [this.lastID, course.price], (err) => { res.json(...) });
    });
  });
});
```

Depois:

```javascript
// database/connection.js — adaptador de Promises sobre o driver de callbacks
const run = (sql, params = []) => new Promise((resolve, reject) =>
  db.run(sql, params, function (err) { err ? reject(err) : resolve({ lastID: this.lastID, changes: this.changes }); }));
const get = (sql, params = []) => new Promise((resolve, reject) =>
  db.get(sql, params, (err, row) => (err ? reject(err) : resolve(row))));

// services/checkoutService.js
async function checkout({ name, email, password, courseId, card }) {
  const course = await courseModel.findActiveById(courseId);
  if (!course) throw new AppError(404, 'Curso não encontrado');
  const user = (await userModel.findByEmail(email)) ?? (await userModel.create({ name, email, password }));
  return enroll(user.id, course, card);
}
```

Passos:
1. Envolva a API de callbacks do driver em funções que devolvem Promise (uma vez, na infraestrutura).
2. Reescreva o fluxo de cima para baixo com `await`; cada erro vira `throw` e chega ao handler central (T-13).
3. Operações independentes em paralelo usam `Promise.all`; contadores manuais desaparecem.
4. Garanta uma única resposta por requisição.

## T-17 — Higiene: constantes, nomes, logger, código morto

Antes:

```python
import os, sys, json
if faturamento > 10000:
    desconto = faturamento * 0.1
print("Produto criado com ID: " + str(id))
```

Depois:

```python
import logging
logger = logging.getLogger(__name__)

FAIXAS_DESCONTO = ((10000, 0.10), (5000, 0.05), (1000, 0.02))   # (faturamento mínimo, percentual)

desconto = next((faturamento * pct for minimo, pct in FAIXAS_DESCONTO if faturamento > minimo), 0)
logger.info("Produto criado: id=%s", produto_id)
```

Passos:
1. **Constantes**: literal de regra de negócio ganha nome e mora no módulo dono da regra. Lista repetida (status, papéis) vira constante única; se já existe constante no projeto, use-a.
2. **Nomes**: renomeie variáveis locais crípticas para o que representam; não sombreie builtins. Não renomeie campos de requisição/resposta nem colunas (contrato).
3. **Log**: troque `print`/`console.log` de aplicação pelo logger do framework ou da biblioteca padrão; sem dados pessoais ou segredos.
4. **Código morto**: remova imports, funções, parâmetros e dependências do manifesto sem uso — depois de confirmar por busca que ninguém usa.
5. Simplifique booleanos verbosos (`if x: return True else: return False` → `return x`).

---

## Ordem de aplicação

1. T-01 (config) → T-09 (dados sem estado global)
2. T-05 (decomposição) junto com T-02, T-10, T-11, T-15 dentro dos models
3. T-03, T-04 (senha e serialização)
4. T-07, T-08, T-12 (controllers, camadas, validação) e T-16 quando houver callbacks
5. T-13 (erros) → T-06 (guardas)
6. T-14 (deprecated) → T-17 (higiene)

Depois de cada bloco, verifique que o projeto importa/compila antes de seguir.
