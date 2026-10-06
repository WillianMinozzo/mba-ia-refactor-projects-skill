================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript + Express 4.18 (SQLite em memória / driver sqlite3)
Files:   3 analyzed | ~180 lines of code
Date:    2026-10-06

## Summary
CRITICAL: 5 | HIGH: 5 | MEDIUM: 7 | LOW: 4

## Findings

### [CRITICAL] F-01 — Credenciais e segredos hardcoded
Pattern: AP-01
File: src/utils.js:2-5
Description: O objeto `config` tem literais de credenciais: `dbUser` ('admi…ster'), `dbPass` ('senh…_123'), `paymentGatewayKey` com prefixo de chave real ('pk_l…cdef') e `smtpUser`.
Impact: Quem tem acesso ao repositório tem as credenciais de banco e a chave do gateway de pagamento. Trocar a chave exige um commit, e ela continua no histórico do git.
Recommendation: Criar um módulo de config que lê do ambiente, um `.env.example` com placeholders e remover os literais do código (T-01).

### [CRITICAL] F-02 — Armazenamento inseguro de senha
Pattern: AP-03
File: src/utils.js:17-23
File: src/AppManager.js:18, 68-69
Description: `badCrypto` concatena 10000 vezes os 2 primeiros caracteres do base64 da senha e corta em 10 caracteres. Assim, o "hash" depende só do começo da senha, é reversível e não tem salt. No checkout, quem não manda `pwd` recebe a senha padrão "123456" (68). O seed grava a senha '123' em texto puro (18).
Impact: Senhas que começam com o mesmo caractere produzem o mesmo hash. Um vazamento da tabela `users` expõe todas as credenciais, e contas criadas sem `pwd` têm senha conhecida.
Recommendation: Usar `crypto.scrypt` com salt aleatório (biblioteca padrão do Node), não definir senha padrão e gravar o seed já com hash (T-03).

### [CRITICAL] F-03 — Exposição de dados sensíveis em log
Pattern: AP-04
File: src/AppManager.js:45
Description: `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` registra o número completo do cartão e a chave do gateway a cada checkout.
Impact: O PAN do cartão e a chave de produção vão para stdout e para qualquer agregador de logs, o que viola o PCI-DSS. Quem lê os logs consegue usar a chave.
Recommendation: Remover o log ou registrar só os 4 últimos dígitos, nunca a chave (T-04).

### [CRITICAL] F-04 — God Class
Pattern: AP-05
File: src/AppManager.js:4-139
Description: `AppManager` concentra a conexão com o banco (7), o DDL das 5 tabelas (12-16), o seed (18-21), o registro de todas as rotas em um único método `setupRoutes` (25-138), a regra de pagamento (46), o cadastro de usuário, a matrícula, a auditoria e o relatório financeiro. O handler de checkout tem 51 linhas (28-78) e 7 níveis de aninhamento.
Impact: Não dá para testar uma regra sem subir o banco e o Express. Qualquer mudança em um domínio pode quebrar os outros.
Recommendation: Separar em config, database (connection/schema/seed), models por entidade, services, controllers e rotas (T-05).

### [CRITICAL] F-05 — Controle de acesso ausente
Pattern: AP-06
File: src/AppManager.js:80, 131
Description: `GET /api/admin/financial-report` devolve a receita e o nome de todos os alunos de cada curso, e `DELETE /api/users/:id` apaga qualquer usuário. Nenhuma das duas tem verificação de credencial, e o projeto não tem nenhum middleware de autenticação.
Impact: Um cliente HTTP anônimo lê os dados financeiros e pessoais de todos os alunos e apaga usuários arbitrários.
Recommendation: Criar um middleware de guarda administrativa (token vindo do ambiente) para essas duas rotas. Autenticação geral fica fora do escopo (T-06).

### [HIGH] F-06 — Regra de negócio e acesso a dados nas rotas
Pattern: AP-07
File: src/AppManager.js:28-78, 80-129, 131-137
Description: Os três handlers chamam `this.db.get/run/all` diretamente. O handler de checkout decide se o pagamento é aprovado (`cc.startsWith("4")`, 46), cria o usuário, faz o hash da senha, grava a matrícula, o pagamento e a auditoria (57). O handler do relatório calcula a receita (108-110) e monta a resposta campo a campo (90, 112-115).
Impact: As regras de pagamento e de receita ficam presas ao HTTP. Não são reutilizáveis nem testáveis isoladamente.
Recommendation: Controllers só leem a entrada, chamam um service/model e devolvem a resposta. SQL vai para models e regras vão para services (T-07).

### [HIGH] F-07 — Camadas ausentes e módulo com responsabilidade trocada
Pattern: AP-08
File: src/AppManager.js:25-138
File: src/utils.js:1-25
Description: Não existe nenhuma camada entre a rota e o banco (não há models, controllers nem services). `utils.js` não é um módulo utilitário: ele guarda a configuração da aplicação (1-7), um cache de estado (9-15) e a função de senha (17-23).
Impact: Não existe lugar óbvio para cada responsabilidade, então cada mudança acaba voltando para `AppManager`.
Recommendation: Criar as camadas MVC e distribuir o conteúdo de `utils.js` entre `config/` e `utils/password` (T-08).

### [HIGH] F-08 — Estado global mutável e dependências sem injeção
Pattern: AP-09
File: src/utils.js:9-10, 12-15, 25
File: src/AppManager.js:7
Description: `globalCache` é um objeto de módulo que cresce sem limite a cada checkout (`logAndCache`, 14). `totalRevenue` é um primitivo exportado que nunca muda para quem o importa. A conexão é criada dentro do construtor (`new sqlite3.Database(':memory:')`), sem como substituí-la.
Impact: O cache vaza memória e ninguém o lê. Não é possível injetar outro banco nos testes.
Recommendation: Remover o estado global e passar a conexão por injeção a partir do composition root (T-09).

### [HIGH] F-09 — Configuração de execução fixa no código
Pattern: AP-10
File: src/utils.js:6
Description: `port: 3000` é literal e não lê `process.env.PORT`. O caminho do banco (`':memory:'`, AppManager.js:7) também é fixo.
Impact: Não dá para mudar a porta ou o banco por ambiente sem editar o código.
Recommendation: Ler `PORT` e `DB_PATH` do ambiente, mantendo 3000 e `:memory:` como padrão (T-01).

### [HIGH] F-10 — Escrita em várias etapas sem transação
Pattern: AP-11
File: src/AppManager.js:50-63, 69-71, 133
Description: O checkout faz INSERT em `users`, `enrollments`, `payments` e `audit_logs` em callbacks independentes, sem BEGIN/COMMIT/ROLLBACK. Se o pagamento falhar (55), a matrícula já gravada fica sem pagamento. O DELETE de usuário (133) deixa `enrollments` e `payments` órfãos, e a própria resposta admite isso (135).
Impact: O banco fica inconsistente em falhas parciais: matrícula sem pagamento ou matrículas de usuário inexistente. Isso distorce o relatório financeiro.
Recommendation: Envolver o checkout em uma transação com rollback e apagar os filhos do usuário dentro de uma transação (T-10).

### [MEDIUM] F-11 — Matrícula duplicada permitida
Pattern: AP-00
File: src/AppManager.js:50
Description: O checkout não verifica se o usuário já está matriculado no curso: o mesmo e-mail pode comprar o mesmo curso várias vezes, e cada compra gera uma nova matrícula e um novo pagamento.
Impact: Cobranças duplicadas e o aluno aparece repetido no relatório financeiro.
Recommendation: Verificar se já existe matrícula antes de cobrar. Isso muda o comportamento de uma requisição que hoje responde 200, então exige decisão de produto (T-07).

### [MEDIUM] F-12 — Queries N+1 no relatório financeiro
Pattern: AP-12
File: src/AppManager.js:83, 92, 104, 106
Description: Para cada curso há uma query de matrículas (92), e para cada matrícula uma query de usuário (104) e outra de pagamento (106). São 1 + C + 2·E queries.
Impact: O tempo do relatório cresce linearmente com o número de matrículas, e o relatório fica em uma rota sem cache.
Recommendation: Uma única query com LEFT JOIN de courses → enrollments → users → payments, agregada em memória (T-11).

### [MEDIUM] F-13 — Validação de entrada insuficiente
Pattern: AP-13
File: src/AppManager.js:35, 132
Description: O checkout só verifica se `usr`, `eml`, `c_id` e `card` existem. Não valida o formato do e-mail, nem que `card` é uma string de dígitos (se `card` for número, `cc.startsWith` lança TypeError e o processo responde 500/cai), nem o tipo de `c_id`. O `:id` do DELETE não é validado.
Impact: Um payload malformado derruba o handler com uma exceção não tratada.
Recommendation: Criar uma função de validação dedicada, chamada pelo controller, que mantém o 400 "Bad Request" do contrato atual (T-12).

### [MEDIUM] F-14 — Tratamento de erro ausente ou incorreto
Pattern: AP-14
File: src/AppManager.js:38, 57, 92-93, 104, 106, 133-135
Description: O `err` dos callbacks é ignorado em 57, 92 (e `enrollments.length` lança se houver erro), 104, 106 e 133. O DELETE responde sucesso mesmo com erro ou id inexistente. Na linha 38, um erro de banco vira 404. Não existe nenhum middleware de erro central.
Impact: Exceções dentro de callbacks do sqlite derrubam o processo inteiro, e o cliente recebe sucesso em operações que falharam.
Recommendation: Usar Promises com async/await e um middleware de erro de 4 argumentos (T-13).

### [MEDIUM] F-15 — Infraestrutura misturada
Pattern: AP-17
File: src/AppManager.js:7, 10-23
Description: O DDL (12-16) e o seed (18-21) ficam no mesmo método `initDb` da classe que registra rotas e rodam a cada boot. O banco é sempre `:memory:`.
Impact: Não é possível ter persistência nem trocar o schema sem mexer na classe das rotas.
Recommendation: Separar `database/connection`, `database/schema` e `database/seed`, todos chamados pelo entry point (T-09).

### [MEDIUM] F-16 — Callback hell
Pattern: AP-18
File: src/AppManager.js:26, 37-77, 86-122
Description: `const self = this` (26) existe só para atravessar callbacks. O checkout tem 7 níveis de callbacks aninhados. O relatório usa contadores manuais (`coursesPending--`, `enrPending--`) e o bloco `report.push … res.json(report)` aparece duplicado (96-98 e 119-121).
Impact: O fluxo fica difícil de seguir, e qualquer erro no contador gera uma resposta que nunca é enviada ou é enviada duas vezes.
Recommendation: Envolver o driver em Promises e reescrever com async/await (T-16).

### [MEDIUM] F-17 — Contrato de resposta inconsistente
Pattern: AP-19
File: src/AppManager.js:35, 38, 41, 48, 51, 55, 60, 70, 84, 87, 135
Description: Os erros saem como texto puro (`res.send("Erro DB")`…) e os sucessos como JSON (60, 87). O DELETE devolve texto. Erro de banco responde 404 (38).
Impact: Os clientes precisam tratar dois formatos e não conseguem distinguir "curso inexistente" de falha do banco.
Recommendation: Centralizar o envio de erros mantendo os status e textos atuais. Padronizar em JSON fica como recomendação, porque mudaria o contrato (T-13).

### [LOW] F-18 — Números e strings mágicos
Pattern: AP-20
File: src/AppManager.js:46, 48, 54, 68, 108
File: src/utils.js:19, 22
Description: O prefixo de aprovação de cartão é `"4"` (46). Os status `'PAID'` e `'DENIED'` aparecem inline (46, 48, 108). A senha padrão é `"123456"` (68). As iterações `10000` (19) e o tamanho `10` (22) estão em `badCrypto`.
Impact: A regra de aprovação e os status ficam espalhados pelo código, e mudar um deles exige caçar literais.
Recommendation: Criar constantes nomeadas no model de pagamento (T-17).

### [LOW] F-19 — Nomenclatura ruim
Pattern: AP-21
File: src/AppManager.js:4, 29-33
File: src/utils.js:17
Description: As variáveis `u`, `e`, `p`, `cid` e `cc` (29-33) são opacas. `AppManager` e `badCrypto` não descrevem o que fazem.
Impact: A leitura do fluxo de checkout depende de adivinhar o que cada letra significa.
Recommendation: Renomear internamente (`name`, `email`, `password`, `courseId`, `cardNumber`). As chaves do corpo (`usr`, `eml`…) continuam, por serem contrato (T-17).

### [LOW] F-20 — Log por console.log
Pattern: AP-22
File: src/AppManager.js:45
File: src/utils.js:13
File: src/app.js:13
Description: Os logs de aplicação usam `console.log` sem nível e, em 45, com dados sensíveis (ver F-03).
Impact: Não dá para filtrar os logs por severidade nem desligá-los em produção.
Recommendation: Criar um logger mínimo com níveis, sem dados sensíveis (T-17).

### [LOW] F-21 — Código morto e símbolos não usados
Pattern: AP-23
File: src/AppManager.js:2
File: src/utils.js:2-3, 5, 9-10, 25
Description: `totalRevenue` é importado (AppManager.js:2) e nunca usado. `dbUser`, `dbPass` e `smtpUser` não são lidos em lugar nenhum. `globalCache` é exportado e só recebe escrita.
Impact: O código sugere integrações (SMTP, banco autenticado) que não existem e confunde quem mantém o projeto.
Recommendation: Remover os símbolos e o cache sem leitor (T-17).

## Deprecated APIs
None detected (checked against Node.js core APIs used — Buffer.from, String.prototype.substring/startsWith —, Express ^4.18.2 — express.json(), res.status().send/json(), app.delete() — and sqlite3 ^5.1.6).

## Proposed Target Structure
```
src/
├── app.js                         # composition root (mantido: node src/app.js)
├── config/index.js                # [novo] PORT, DB_PATH, PAYMENT_GATEWAY_KEY, ADMIN_TOKEN via env
├── database/
│   ├── connection.js              # [novo] abre sqlite3 + wrappers Promise (run/get/all/transaction)
│   ├── schema.js                  # [novo] DDL
│   └── seed.js                    # [novo] dados iniciais (senha com hash)
├── models/
│   ├── userModel.js               # [novo]
│   ├── courseModel.js             # [novo]
│   ├── enrollmentModel.js         # [novo]
│   ├── paymentModel.js            # [novo] status e regra de aprovação
│   └── auditLogModel.js           # [novo]
├── services/
│   ├── checkoutService.js         # [novo] usuário + matrícula + pagamento + auditoria em transação
│   └── financialReportService.js  # [novo] relatório via JOIN único
├── controllers/
│   ├── checkoutController.js      # [novo]
│   ├── adminController.js         # [novo]
│   └── userController.js          # [novo]
├── routes/index.js                # [novo] mapeamento HTTP → controllers
├── middlewares/
│   ├── adminAuth.js               # [novo] guarda das rotas administrativas
│   └── errorHandler.js            # [novo] tratamento central de erros
└── utils/
    ├── password.js                # [novo] scrypt + salt (substitui badCrypto)
    └── logger.js                  # [novo] logger com níveis
.env.example                       # [novo]
```
`AppManager.js` e `utils.js` deixam de existir: o conteúdo deles é distribuído pelas camadas acima. O entry point `src/app.js` e o comando `npm start` continuam os mesmos.

================================
Total: 21 findings
================================
