# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`, já refatorada para MVC.

## Como rodar

```bash
pip install -r requirements.txt
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000`. O `seed.py` popula o banco SQLite (`instance/tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias.

## Configuração

Todas as variáveis são opcionais em desenvolvimento; veja `.env.example` (copie para `.env`).

| Variável | Padrão | Uso |
|---|---|---|
| `APP_ENV` | `development` | `production` exige `SECRET_KEY` e fecha rotas admin sem `ADMIN_TOKEN` |
| `SECRET_KEY` | efêmera (gerada no boot) | assinatura do token de login |
| `DATABASE_URL` | `sqlite:///tasks.db` | URI do banco |
| `DEBUG` | `false` | modo debug do Flask |
| `HOST` / `PORT` | `0.0.0.0` / `5000` | bind do servidor |
| `CORS_ORIGINS` | `*` | origens permitidas, separadas por vírgula |
| `ADMIN_TOKEN` | — | quando definido, `/reports/*`, `DELETE /users/<id>` e a atribuição de `role` exigem o header `X-Admin-Token` |

## Estrutura

```
app.py            composition root (create_app) + execução
seed.py           comando de seed → database/seed.py
config/           leitura do ambiente
database/         sessão do ORM, schema, seed
models/           entidades, consultas e regras de domínio (+ errors.py)
services/         relatórios (vários models) e emissão de token
controllers/      fluxo requisição → model/service → resposta
routes/           blueprints (mapeamento URL → controller)
middlewares/      tratamento de erro central e guarda admin
utils/            helpers genéricos
```
