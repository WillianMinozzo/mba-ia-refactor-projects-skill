# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo (senhas gravadas com hash).

## Configuração

Toda configuração vem de variáveis de ambiente; veja `.env.example`. Sem nenhuma variável definida, a aplicação sobe em modo de desenvolvimento, com debug desligado e uma `SECRET_KEY` efêmera.

As rotas `/admin/*` exigem o header `X-Admin-Token` igual a `ADMIN_TOKEN`. Sem `ADMIN_TOKEN` definido, elas respondem 403.

## Estrutura

```
app.py          composition root (create_app) e boot
config/         leitura do ambiente
database/       conexão por requisição, schema e seed
models/         acesso a dados e regras de domínio (um arquivo por entidade)
services/       fluxo de pedido e notificações
validators/     validação da entrada HTTP
controllers/    orquestração requisição → model/service → resposta
routes/         mapeamento URL → controller (Blueprints)
middlewares/    tratamento de erro central e guarda administrativa
```
