================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript + Express 4 (SQLite / driver sqlite3 com adaptador de Promises)
Files:   31 analyzed | ~580 lines of code
Date:    2026-10-06

## Summary
CRITICAL: 1 | HIGH: 3 | MEDIUM: 3 | LOW: 2

## Findings

### [CRITICAL] F-01 — Guarda administrativa quebra o contrato no boot padrão
Pattern: AP-00
File: src/middlewares/adminAuth.js:7-15
File: src/config/index.js:17-18
File: src/routes/adminRoutes.js:6
File: src/routes/userRoutes.js:6
File: src/app.js:29
File: README.md:18
File: .env.example:11-13
Description: requireAdmin responde 403 'Rota administrativa desabilitada' (adminAuth.js:10) sempre que config.adminToken está vazio, e esse é o valor padrão (config/index.js:18). Com isso, GET /api/admin/financial-report (read) e DELETE /api/users/:id (write de um único recurso, não destructive) passam a exigir configuração nova para responder. No original (HEAD:src/AppManager.js:80, 131), as duas rotas respondiam 200. A documentação (README.md:18, .env.example:11-13) registra esse comportamento como se fosse o esperado.
Impact: Com `npm start` sem variáveis novas, 2 das 3 rotas do contrato deixam de funcionar (200 → 403) para todos os clientes. O relatório financeiro e a exclusão de usuário ficam inutilizáveis sem uma configuração que o boot original não pedia.
Recommendation: Exigir X-Admin-Token só quando ADMIN_TOKEN estiver configurado (401 sem o header, comportamento original com ele). Sem token e fora de produção, deixar passar e avisar em log. Em NODE_ENV=production sem token, manter 403. Atualizar README e .env.example (T-06).

### [HIGH] F-02 — Transação não isolada na conexão única compartilhada
Pattern: AP-00
File: src/database/connection.js:5-6, 8-18, 25-39
Description: transaction() enfileira apenas as outras transações (transactionQueue). Já run/get/all, chamados fora de transação, vão direto para a mesma conexão `raw`. Assim, um `DELETE FROM users` (userModel.remove) emitido por outra requisição enquanto um checkout está entre BEGIN e COMMIT entra na transação do checkout.
Impact: Se o checkout falhar e fizer ROLLBACK, a exclusão concorrente é desfeita, mas o cliente já recebeu 200. Leituras concorrentes (relatório financeiro) também enxergam linhas ainda não confirmadas.
Recommendation: Serializar as operações avulsas atrás da fila de transações e deixar passar direto apenas o que roda dentro da transação ativa, identificada por AsyncLocalStorage (stdlib) (T-10).

### [HIGH] F-03 — Exclusão de usuário deixa matrículas e pagamentos órfãos
Pattern: AP-11
File: src/models/userModel.js:14-17
File: src/controllers/userController.js:4-6
File: src/database/schema.js:4-5
Description: userModel.remove executa apenas `DELETE FROM users WHERE id = ?`. As tabelas enrollments e payments não têm FOREIGN KEY nem ON DELETE CASCADE, e nada remove os filhos. O comentário do controller registra a limpeza como "adiada".
Impact: Depois de um DELETE, o relatório financeiro continua contando a receita do usuário removido e o lista como 'Unknown'. Os pagamentos ficam sem dono rastreável.
Recommendation: Remover payments → enrollments → user em uma única transação no model, mantendo o texto de resposta, que faz parte do contrato (T-10).

### [HIGH] F-04 — Checkout lê o usuário fora da transação (corrida cria duplicados)
Pattern: AP-11
File: src/services/checkoutService.js:13, 19, 21-22
File: src/database/schema.js:2
Description: users.findByEmail (linha 13) roda antes de db.transaction (linha 21), e users.create (linha 22) decide com base nessa leitura antiga. A coluna users.email não tem restrição UNIQUE.
Impact: Dois checkouts simultâneos com o mesmo e-mail novo criam dois usuários. As matrículas ficam divididas entre eles e findByEmail passa a retornar um dos dois de forma arbitrária.
Recommendation: Refazer a busca do usuário dentro da transação, que já é serializada, e reaproveitar o usuário encontrado. Manter o hash calculado antes da transação para não segurar a fila (T-10).

### [MEDIUM] F-05 — Validação mais restritiva que o contrato original, sem declaração
Pattern: AP-00
File: src/validators/checkoutValidator.js:4-5, 13-15
File: src/validators/userValidator.js:4-8
Description: O original validava só a presença de usr, eml, c_id e card (HEAD:src/AppManager.js:35) e aceitava qualquer :id no DELETE (HEAD:src/AppManager.js:131-136). Hoje EMAIL_PATTERN, CARD_PATTERN (`^\d{1,19}$`), toPositiveInteger e a exigência de string respondem 400 onde antes havia 200 ou 404. Exemplos: card "4111 2222 3333 4444" (antes 200), eml "gui" (antes 200), c_id "abc" (antes 404), DELETE /api/users/abc (antes 200).
Impact: Clientes que funcionavam passam a receber 400. Nenhuma dessas mudanças está entre as exceções permitidas (correções de segurança) nem foi declarada.
Recommendation: Rejeitar com 400 só o que o original rejeitava (campo ausente ou falsy). Manter as guardas de tipo apenas onde o original derrubava o processo (card ou pwd não-string). c_id não numérico deve seguir para 404. :id inválido deve responder como antes (T-12).

### [MEDIUM] F-06 — Configuração lida fora do módulo de config
Pattern: AP-17
File: src/utils/logger.js:2
File: src/config/index.js:13-20
Description: logger.js lê process.env.LOG_LEVEL diretamente, e o módulo de config não expõe logLevel, embora LOG_LEVEL esteja documentado em .env.example.
Impact: Existem duas fontes de configuração. O nível de log não aparece junto com o resto da config e não pode ser injetado em testes.
Recommendation: Expor logLevel em config/index.js e fazer o logger consumi-lo (T-01, T-09).

### [MEDIUM] F-07 — Contrato de resposta misto (JSON no sucesso, texto puro nos erros)
Pattern: AP-19
File: src/controllers/checkoutController.js:8
File: src/controllers/userController.js:14
File: src/middlewares/errorHandler.js:12-15
File: src/middlewares/adminAuth.js:10, 13
Description: POST /api/checkout responde JSON no sucesso. DELETE /api/users/:id e todos os erros respondem texto puro.
Impact: Clientes precisam tratar dois formatos. O formato é herdado do original e faz parte do contrato atual.
Recommendation: Manter: o tratamento já está centralizado em errorHandler. Padronizar o corpo para JSON muda o contrato e fica como recomendação para uma versão nova da API (T-13).

### [LOW] F-08 — Números mágicos de tamanho de segredo
Pattern: AP-20
File: src/config/index.js:10
File: src/utils/password.js:25
Description: crypto.randomBytes(32) em secret() e crypto.randomBytes(18) em randomPassword() usam literais. Os outros tamanhos de password.js já são constantes nomeadas (SALT_BYTES, KEY_LENGTH).
Impact: Inconsistência pequena de legibilidade.
Recommendation: Extrair para constantes nomeadas (T-17).

### [LOW] F-09 — Código morto
Pattern: AP-23
File: src/utils/password.js:15-21, 28
File: src/database/connection.js:20-21, 41
Description: verifyPassword é exportada e não tem nenhum importador. close() da conexão é exportada e nunca é chamada (grep em src/).
Impact: Superfície de código sem uso, mantida e revisada à toa.
Recommendation: Remover verifyPassword. Remover close() ou usá-lo em um desligamento ordenado; preferir remover, porque o banco padrão é em memória (T-17).

## Deprecated APIs
None detected (checked against Node.js v24.4.1, Express 4.22.1 (^4.18.2), sqlite3 5.1.7 (^5.1.6)).

## Proposed Target Structure
```
src/
├── app.js                          (mantido)  composition root + listen
├── config/index.js                 (alterado) + logLevel; constante para tamanho do segredo
├── database/
│   ├── connection.js               (alterado) fila única + AsyncLocalStorage; sem close()
│   ├── schema.js                   (mantido)
│   └── seed.js                     (mantido)
├── models/
│   ├── userModel.js                (alterado) remove() em transação com cascata
│   ├── courseModel.js · enrollmentModel.js · paymentModel.js · auditLogModel.js · index.js  (mantidos)
├── services/
│   ├── checkoutService.js          (alterado) busca do usuário dentro da transação
│   ├── financialReportService.js · paymentGateway.js · index.js  (mantidos)
├── controllers/
│   ├── userController.js           (alterado) comentário de "adiado" removido
│   ├── checkoutController.js · adminController.js · index.js  (mantidos)
├── validators/
│   ├── checkoutValidator.js        (alterado) regras alinhadas ao contrato original
│   ├── userValidator.js            (alterado) :id inválido não responde 400
│   └── common.js                   (mantido/ajustado)
├── routes/ (checkoutRoutes.js · adminRoutes.js · userRoutes.js · index.js)  (mantidos)
├── middlewares/
│   ├── adminAuth.js                (alterado) guarda exigida só com ADMIN_TOKEN configurado
│   └── errorHandler.js             (mantido)
└── utils/
    ├── logger.js                   (alterado) nível vindo da config
    ├── password.js                 (alterado) sem verifyPassword; constante nomeada
    └── errors.js                   (mantido)
```
O projeto já está em N2 com as camadas corretas: nenhuma pasta é criada nem renomeada. As correções ficam dentro das camadas existentes. Também serão atualizados README.md e .env.example para a nova semântica de ADMIN_TOKEN.

================================
Total: 9 findings
================================
