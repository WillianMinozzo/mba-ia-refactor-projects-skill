# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e já carrega seeds automaticamente no boot.

## Configuração

As variáveis de ambiente estão documentadas em `.env.example` (`PORT`, `DB_FILE`, `PAYMENT_GATEWAY_KEY`, `ADMIN_TOKEN`, `LOG_LEVEL`, `NODE_ENV`).

As rotas administrativas (`GET /api/admin/financial-report` e `DELETE /api/users/:id`) passam a exigir o header `X-Admin-Token` quando `ADMIN_TOKEN` está definido (`401` sem ele). Sem a variável, fora de produção elas respondem como sempre (com aviso no log de boot); com `NODE_ENV=production`, respondem `403`.

`DELETE /api/users/:id` remove o usuário junto com suas matrículas e pagamentos, em uma única transação.

## Estrutura

```
src/
├── app.js           # composition root e boot
├── config/          # leitura do ambiente
├── database/        # conexão (Promises + transação), schema e seed
├── models/          # acesso a dados, um por entidade
├── services/        # checkout (transação), relatório financeiro, gateway de pagamento
├── controllers/     # entrada → service/model → resposta
├── validators/      # validação de entrada
├── routes/          # mapeamento HTTP (express.Router)
├── middlewares/     # erro centralizado e guarda administrativa
└── utils/           # logger, hash de senha (scrypt), erros de domínio
```

Exemplos de requisições estão em `api.http`.
