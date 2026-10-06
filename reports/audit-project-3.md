================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0 (SQLite / Flask-SQLAlchemy 3.1.1 ORM)
Files:   15 analyzed | ~1158 lines of code
Date:    2026-10-06

## Summary
CRITICAL: 4 | HIGH: 4 | MEDIUM: 7 | LOW: 4

## Findings

### [CRITICAL] F-01 — Credenciais e segredos hardcoded
Pattern: AP-01
File: app.py:13
File: services/notification_service.py:9-10
Description: `app.config['SECRET_KEY'] = 'supe…123'` está fixo no entry point. `NotificationService.__init__` grava `email_user = 'taskmanager@gmail.com'` e `email_password = 'sen…123'` (SMTP do Gmail) como literais.
Impact: Quem lê o repositório pode assinar sessões/tokens com a SECRET_KEY e entrar na conta SMTP. Depois que o projeto passar a emitir token assinado, uma chave conhecida permite forjar o token de qualquer usuário.
Recommendation: Ler SECRET_KEY e as credenciais SMTP do ambiente via `config/settings.py`; em desenvolvimento, gerar uma chave efêmera quando ela não estiver definida; publicar `.env.example` (T-01).

### [CRITICAL] F-02 — Armazenamento inseguro de senha
Pattern: AP-03
File: models/user.py:27-32
File: seed.py:19, 26, 33
File: routes/user_routes.py:64, 115
Description: `set_password` usa `hashlib.md5(pwd.encode()).hexdigest()` sem salt. `check_password` compara com `==`. O seed cria usuários com as senhas '1234', 'abcd' e 'pass', e as rotas aceitam senhas a partir de 4 caracteres.
Impact: Com o hash vazando (ver F-03), senhas curtas em MD5 sem salt caem por tabela rainbow em segundos, inclusive a do admin do seed.
Recommendation: Usar `werkzeug.security.generate_password_hash`/`check_password_hash` (já instalado com o Flask). Manter a verificação de hashes MD5 legados e regravá-los no próximo login (T-03).

### [CRITICAL] F-03 — Exposição de dados sensíveis
Pattern: AP-04
File: models/user.py:16-25
File: routes/user_routes.py:33, 85, 129, 209
Description: `User.to_dict()` inclui `'password': self.password` (linha 21). Esse dicionário é devolvido em GET /users/<id> (33), POST /users (85), PUT /users/<id> (129) e POST /login (209).
Impact: Qualquer cliente anônimo obtém o hash MD5 da senha de qualquer usuário consultando `/users/1`, `/users/2` e assim por diante.
Recommendation: Remover `password` da serialização do model. É uma mudança intencional de contrato (T-04).

### [CRITICAL] F-04 — Controle de acesso ausente ou falso
Pattern: AP-06
File: routes/user_routes.py:52, 71-72, 78, 119-122, 210
Description: POST /users aceita `role` do corpo (52, 78), inclusive `'admin'`. PUT /users/<id> permite trocar `role` (119-122). O login devolve `'fake-jwt-token-' + str(user.id)` (210), um token previsível que nada valida. Nenhuma rota do projeto tem guarda; os blueprints são registrados sem middleware (app.py:18-20).
Impact: Um cliente anônimo cria um usuário admin ou se promove a admin, e consegue "forjar" o token de qualquer id. Qualquer guarda futura baseada em role ou token nasce comprometida.
Recommendation: Ignorar role elevado vindo do cliente sem credencial de admin, emitir um token assinado com SECRET_KEY e adicionar uma guarda opcional (`ADMIN_TOKEN`) para as rotas administrativas. Exigir autenticação em todas as rotas fica adiado porque muda o contrato (T-06).

### [HIGH] F-05 — God Method (handlers-deus)
Pattern: AP-05
File: routes/report_routes.py:12-101
File: routes/task_routes.py:11-63
Description: `summary_report` tem 90 linhas e consulta Task, User e Category: 14 contagens, cálculo de atraso, produtividade por usuário e montagem manual do JSON. `get_tasks` tem 53 linhas, 5 níveis de aninhamento (try → for → if → if → if, linhas 13-32) e consultas a 3 entidades.
Impact: Não há como testar a regra de atraso ou de produtividade sem subir HTTP e banco. Pelo critério de desempate, o problema só atrapalha quem mantém o código, por isso fica em HIGH e não em CRITICAL.
Recommendation: Extrair as consultas e agregações para models/`services/report_service.py`, deixando o handler com uma chamada só (T-05).

### [HIGH] F-06 — Regra de negócio e acesso a dados nas rotas
Pattern: AP-07
File: routes/task_routes.py:11-63, 65-83, 85-154, 156-223, 225-238, 240-271, 273-299
File: routes/user_routes.py:10-25, 27-40, 42-90, 92-132, 134-151, 153-183, 185-211
File: routes/report_routes.py:12-101, 103-155, 157-165, 167-188, 190-209, 211-223
Description: Todos os 20 handlers dos blueprints chamam `Model.query`/`db.session` diretamente, aplicam regras de domínio (status válidos, faixa de prioridade, atraso, taxa de conclusão, unicidade de e-mail) e montam o dicionário de resposta campo a campo. Não existe camada de controller.
Impact: Cada regra fica presa a um handler HTTP. Mudar a regra de atraso, por exemplo, exige editar 6 lugares (ver F-14), e nada pode ser testado sem o Flask.
Recommendation: Criar `controllers/` (um por recurso). Queries e regras vão para os models (ou para um service quando envolvem vários), e as rotas ficam só com o mapeamento (T-07).

### [HIGH] F-07 — Camadas mortas e responsabilidades trocadas
Pattern: AP-08
File: routes/report_routes.py:157-223
File: services/notification_service.py:4-48
File: utils/helpers.py:9-108
File: models/task.py:38-60
Description: O CRUD de `/categories` mora no blueprint `reports`. `NotificationService` não é importado por nenhum arquivo. Nenhuma função de `utils/helpers.py` é chamada: `format_date` e `calculate_percentage` são importadas em report_routes.py:7 e nunca usadas, e `process_task_data` reimplementa a validação que as rotas fazem inline. Em `Task`, os métodos `validate_status`, `validate_priority` e `is_overdue` nunca são chamados, enquanto as rotas reescrevem as mesmas regras.
Impact: A estrutura de pastas promete camadas que não funcionam. Quem corrige uma regra no lugar "certo" (model ou helper) não muda o comportamento da API.
Recommendation: Mover categories para um recurso próprio, usar os métodos canônicos do model e remover o service e os helpers sem uso (T-08).

### [HIGH] F-08 — Configuração insegura de execução
Pattern: AP-10
File: app.py:11, 15, 34
Description: `app.run(debug=True, host='0.0.0.0', port=5000)` fixo (34). `CORS(app)` libera qualquer origem (15). A URI do banco é literal (11).
Impact: Com debug ligado e bind em todas as interfaces, qualquer exceção não tratada mostra o depurador do Werkzeug para a rede. Basta `GET /tasks/search?priority=abc` ou `POST /tasks` com `priority` string. Esse depurador permite executar código (protegido apenas por PIN).
Recommendation: Ler debug, host, porta, URI e origens de CORS do ambiente, com debug desligado por padrão e os demais padrões iguais aos atuais (T-01).

### [MEDIUM] F-09 — Queries N+1
Pattern: AP-12
File: routes/task_routes.py:41-57, 275-281
File: routes/user_routes.py:22
File: routes/report_routes.py:15-28, 46-51, 53-56, 159-163
Description: `get_tasks` faz `User.query.get` e `Category.query.get` para cada task. `/tasks/stats` faz 5 COUNTs e ainda carrega todas as tasks. `get_users` usa `len(u.tasks)` (lazy) por usuário. `summary_report` faz 14 COUNTs separados e uma query por usuário. `get_categories` faz um `count()` por categoria.
Impact: GET /tasks executa 1 + 2N queries; o resumo cresce com o número de usuários. Com dados reais, a latência escala de forma linear.
Recommendation: Usar `GROUP BY`/`func.count`, `joinedload`/`selectinload` e agregações no model (T-11).

### [MEDIUM] F-10 — Validação de entrada ausente, duplicada e divergente
Pattern: AP-13
File: routes/task_routes.py:92-114, 166-184, 260-264
File: routes/user_routes.py:61, 102-103, 106, 124-125
File: routes/report_routes.py:180, 196-202
File: utils/helpers.py:57-108
Description: `priority < 1` é comparado sem checar o tipo (113, 182): uma string gera TypeError e 500. `len(data['title'])` recebe None (167). `int(priority)`/`int(user_id)` da query string ficam sem tratamento (261, 264). `update_category` usa `'name' in data` com `data` possivelmente None (196-197). `color` não é validada (180, 202), embora `is_valid_color` exista. `name` e `active` do usuário são aceitos sem validação (102-103, 124-125). As regras de task estão copiadas entre create e update e divergem de `process_task_data` (que faz strip e aceita dd/mm/aaaa).
Impact: Entradas mal formadas viram 500 com stack trace em vez de 400, e o mesmo campo segue regras diferentes conforme a rota.
Recommendation: Uma validação por recurso, chamada pelo controller, preservando mensagens e status atuais e convertendo os casos que hoje dão 500 por tipo inválido (T-12).

### [MEDIUM] F-11 — Tratamento de erro genérico e repetido
Pattern: AP-14
File: routes/task_routes.py:62-63, 137, 151-154, 204, 221-223, 236-238
File: routes/user_routes.py:87-90, 130-132, 149-151
File: routes/report_routes.py:186-188, 207-209, 221-223
File: utils/helpers.py:46, 49, 88
File: app.py:9-31
Description: Há 13 `except:` sem tipo e o mesmo bloco `try/commit/except → rollback + 500` copiado em 9 handlers. `get_tasks` engole qualquer erro (62). app.py não registra nenhum `errorhandler`.
Impact: Bugs reais ficam mascarados como "Erro interno". Erros fora de `try` escapam para o depurador (F-08). Cada handler novo repete o boilerplate.
Recommendation: Criar um handler central em `middlewares/error_handler.py` com exceções de domínio nomeadas e o mesmo corpo `{'error': ...}` usado hoje (T-13).

### [MEDIUM] F-12 — APIs deprecated
Pattern: AP-15
File: models/task.py:15, 16, 52
File: models/user.py:14
File: models/category.py:11
File: routes/task_routes.py:31, 42, 51, 67, 72, 117, 122, 158, 188, 195, 215, 227, 285
File: routes/user_routes.py:29, 94, 136, 155, 172
File: routes/report_routes.py:35, 42, 45, 71, 105, 133, 192, 213
File: services/notification_service.py:35
File: utils/helpers.py:38
File: seed.py:66, 67, 69, 70, 74
Description: `datetime.utcnow` é obsoleto no Python 3.12 (runtime em uso). `Model.query.get(id)` é a API legada `Query.get()` no SQLAlchemy 2.x (exigido pelo Flask-SQLAlchemy 3.1.1).
Impact: Gera DeprecationWarning a cada requisição, e a API será removida em versões futuras do Python e do SQLAlchemy.
Recommendation: `datetime.now(timezone.utc)` (gravando naive UTC para manter o formato serializado) e `db.session.get(Model, id)` (T-14).

### [MEDIUM] F-13 — Contrato de resposta inconsistente
Pattern: AP-19
File: routes/task_routes.py:119, 124, 190, 197
Description: Um `user_id`/`category_id` inexistente no **corpo** de POST/PUT /tasks responde 404, o mesmo status de "task não encontrada", em vez de um erro de validação (400/422).
Impact: O cliente não distingue recurso da URL ausente de referência inválida no payload.
Recommendation: Manter 404 para não quebrar clientes e registrar como recomendação de evolução do contrato (T-13).

### [MEDIUM] F-14 — Código duplicado
Pattern: AP-16
File: routes/task_routes.py:17-28, 30-39, 71-80, 110, 177, 275-279, 283-287, 296
File: routes/user_routes.py:61, 106, 162-169, 171-180
File: routes/report_routes.py:19-22, 33-37, 67, 132-135, 151
File: utils/helpers.py:14-17, 21, 75, 110
File: models/task.py:23-36, 39, 50-60
Description: A regra "atrasada" aparece 6 vezes inline, enquanto a canônica é `Task.is_overdue` (models/task.py:50-60). A serialização de task é refeita manualmente (task_routes 17-28, user_routes 162-169), apesar de `Task.to_dict` existir. A lista de status está em 5 lugares, a regex de e-mail em 3, o cálculo de completion_rate em 3 (há `calculate_percentage`) e as contagens por status em 2 rotas.
Impact: Mudar uma regra exige editar até 6 cópias, que já divergem: `process_task_data` aceita formatos que as rotas recusam.
Recommendation: Usar os métodos canônicos do model e remover as cópias (T-15).

### [MEDIUM] F-15 — Infraestrutura misturada
Pattern: AP-17
File: app.py:11-13, 30-31
File: requirements.txt:6
File: seed.py:2
Description: URI, flags e SECRET_KEY são atribuídas no entry point. `db.create_all()` roda como efeito colateral do `import app` (30-31), inclusive quando `seed.py` importa `app` (seed.py:2). `python-dotenv` está declarado e nunca é usado.
Impact: Importar o módulo já cria schema e prende a config. Não há como instanciar a app com outra configuração (testes, outro banco).
Recommendation: `create_app()` em app.py, `config/settings.py` carregando `.env` com python-dotenv, e schema/seed em `database/` chamados explicitamente (T-01, T-09).

### [LOW] F-16 — Números e strings mágicos
Pattern: AP-20
File: routes/task_routes.py:96, 99, 104, 110, 113, 167, 169, 177, 182
File: routes/user_routes.py:64, 71, 115, 120
File: routes/report_routes.py:45, 129, 180
File: utils/helpers.py:110-116
Description: Os limites 3/200 (título), 1..5 (prioridade), 3 (prioridade padrão), 4 (senha), 7 (dias), `<= 2` (alta prioridade), `'#000000'` e as listas de status e roles aparecem como literais. As constantes `VALID_STATUSES`, `VALID_ROLES`, `MIN_TITLE_LENGTH` etc. já existem em helpers.py:110-116 e são ignoradas.
Impact: Um ajuste de regra exige caçar literais espalhados.
Recommendation: Constantes nomeadas no model de cada domínio (T-17).

### [LOW] F-17 — Nomenclatura ruim
Pattern: AP-21
File: routes/task_routes.py:16, 51
File: routes/user_routes.py:14, 37
File: routes/report_routes.py:24-28, 33, 55, 161
File: models/task.py:45
File: models/user.py:27
Description: Usa variáveis `t`, `u`, `c`, `cat`, `p`, `pwd` e `p1`..`p5` para as contagens por prioridade.
Impact: Fica mais difícil ler os handlers longos.
Recommendation: Nomes descritivos ao mover o código para models e controllers (T-17).

### [LOW] F-18 — Log por print
Pattern: AP-22
File: routes/task_routes.py:149, 153, 219, 234
File: routes/user_routes.py:83, 89, 147
File: services/notification_service.py:21, 24
File: utils/helpers.py:39, 41
Description: Eventos e erros da aplicação saem por `print(...)`, sem nível. user_routes.py:83 registra o nome do usuário.
Impact: Não há como filtrar nem silenciar logs, e o erro de commit (89, 153) some no stdout.
Recommendation: `logging.getLogger(__name__)` com níveis (T-17).

### [LOW] F-19 — Código morto, imports e dependências não usados
Pattern: AP-23
File: app.py:7
File: routes/task_routes.py:7
File: routes/user_routes.py:6
File: routes/report_routes.py:7-8
File: models/task.py:3
File: models/user.py:34-38
File: utils/helpers.py:3-7, 57
File: requirements.txt:4-6
Description: Imports sem uso: `os, sys, json` (app.py), `json, os, sys, time` (task_routes), `hashlib, json` (user_routes), `format_date, calculate_percentage, json` (report_routes), `json` (task.py) e `os, json, sys, math, hashlib` (helpers). `User.is_admin` não tem chamador e o parâmetro `existing_task` nunca é lido. `marshmallow`, `requests` e `python-dotenv` não são importados por nenhum arquivo.
Impact: Ruído na leitura e dependências instaladas sem necessidade (superfície de ataque e de atualização).
Recommendation: Remover imports, símbolos e dependências sem uso. python-dotenv passa a ser usado pela config (T-17).

## Deprecated APIs
| API | File | Deprecated since | Replacement |
|-----|------|------------------|-------------|
| `datetime.utcnow()` / `default=datetime.utcnow` | models/task.py:15, 16, 52; models/user.py:14; models/category.py:11; routes/task_routes.py:31, 72, 215, 285; routes/user_routes.py:172; routes/report_routes.py:35, 42, 45, 71, 133; services/notification_service.py:35; utils/helpers.py:38; seed.py:66, 67, 69, 70, 74 | Python 3.12 | `datetime.now(timezone.utc)` |
| `Model.query.get(id)` (`Query.get`) | routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227; routes/user_routes.py:29, 94, 136, 155; routes/report_routes.py:105, 192, 213 | SQLAlchemy 2.0 (legado) | `db.session.get(Model, id)` |

## Proposed Target Structure
```
task-manager-api/
├── app.py                         # [alterado] create_app() + execução (python app.py)
├── seed.py                        # [mantido] wrapper do comando → database/seed.py
├── .env.example                   # [novo]
├── config/
│   ├── __init__.py                # [novo]
│   └── settings.py                # [novo] SECRET_KEY, DATABASE_URL, DEBUG, HOST, PORT, CORS_ORIGINS, ADMIN_TOKEN
├── database/
│   ├── __init__.py                # [novo] reexporta db (from database import db continua válido)
│   ├── connection.py              # [movido de database.py]
│   └── seed.py                    # [movido de seed.py] dados de exemplo
├── models/                        # [mantido] + queries, regras e constantes do domínio
│   ├── __init__.py
│   ├── task.py
│   ├── user.py
│   └── category.py
├── services/
│   ├── __init__.py
│   └── report_service.py          # [novo] agregações Task+User+Category
│   (notification_service.py)      # [removido] nunca usado, credenciais fixas
├── controllers/                   # [novo]
│   ├── __init__.py
│   ├── task_controller.py
│   ├── user_controller.py
│   ├── category_controller.py
│   ├── report_controller.py
│   └── health_controller.py
├── routes/                        # [mantido] só mapeamento URL → controller
│   ├── __init__.py
│   ├── task_routes.py
│   ├── user_routes.py
│   ├── category_routes.py         # [novo] /categories saindo de report_routes
│   ├── report_routes.py
│   └── health_routes.py           # [novo] /health e / saindo de app.py
├── middlewares/                   # [novo]
│   ├── __init__.py
│   ├── error_handler.py           # exceções de domínio → {'error': ...} + status
│   └── auth.py                    # guarda admin opcional (ADMIN_TOKEN) + token assinado
└── utils/
    ├── __init__.py
    └── helpers.py                 # [reduzido] calculate_percentage, validate_email
```
Mantém models/, routes/ e utils/ e os nomes de rotas, campos e blueprints. Cria a camada de controllers, config, middlewares e um service de relatórios. Move categories para um recurso próprio e remove o service de notificação e os helpers mortos.

================================
Total: 19 findings
================================
