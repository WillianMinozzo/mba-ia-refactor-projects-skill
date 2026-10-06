# Refatoração Arquitetural Automatizada — Skill `refactor-arch`

Desafio do MBA em Engenharia de Software com IA (Full Cycle): uma skill que analisa, audita e refatora qualquer projeto backend para o padrão MVC, independente da tecnologia.

- **Ferramenta:** Claude Code (Custom Skills)
- **Skill:** `.claude/skills/refactor-arch/` (idêntica nos 3 projetos)
- **Projetos-alvo:** `code-smells-project` (Python/Flask), `ecommerce-api-legacy` (Node.js/Express), `task-manager-api` (Python/Flask + SQLAlchemy)
- **Base:** [devfullcycle/mba-ia-refactor-projects-skill](https://github.com/devfullcycle/mba-ia-refactor-projects-skill)

| Projeto | Stack detectada | Findings | CRITICAL | HIGH | MEDIUM | LOW | App funciona após a Fase 3 |
|---|---|---|---|---|---|---|---|
| code-smells-project | Python + Flask 3.1.1 (sqlite3) | 22 | 7 | 5 | 6 | 4 | ✅ |
| ecommerce-api-legacy | JavaScript + Express 4.18 (sqlite3) | 21 | 5 | 5 | 7 | 4 | ✅ |
| task-manager-api | Python + Flask 3.0.0 (Flask-SQLAlchemy) | 19 | 4 | 4 | 7 | 4 | ✅ |

---

## A) Análise Manual

Análise feita lendo o código dos três projetos **antes** de escrever a skill. Linhas referentes ao código original (commit `6d1ce62`).

### Projeto 1 — code-smells-project (Python / Flask 3.1.1 / sqlite3 puro)

Domínio: API de e-commerce (produtos, usuários, pedidos, relatório de vendas). 4 arquivos, ~780 linhas.

| # | Sev. | Problema | Arquivo:linha | Por que importa |
|---|------|----------|---------------|-----------------|
| 1 | CRITICAL | SQL Injection por concatenação de strings em todas as queries | `models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-166, 174, 188, 192, 220, 224, 279-281, 289-297` | Qualquer parâmetro vira SQL. Em `109-111` o login é burlável com `' OR '1'='1`. |
| 2 | CRITICAL | Endpoint que executa SQL arbitrário e endpoint que apaga o banco, ambos sem autenticação | `app.py:59-78` (`/admin/query`), `app.py:47-57` (`/admin/reset-db`) | Acesso total de leitura/escrita/destruição dos dados por qualquer cliente HTTP. |
| 3 | CRITICAL | `SECRET_KEY` hardcoded e devolvida no `/health` | `app.py:7`, `controllers.py:289` | Segredo versionado no git e exposto publicamente por um endpoint. |
| 4 | CRITICAL | Senhas em texto puro: gravadas sem hash e retornadas na API | `models.py:126-129` (insert), `models.py:83, 99` (serialização), `database.py:75-79` (seed) | Vazamento direto de credenciais em `GET /usuarios`. |
| 5 | HIGH | God Module: um arquivo com SQL, regra de negócio e serialização de 4 domínios | `models.py:1-314` | Sem coesão; impossível testar um domínio isolado. Regra de desconto (`256-262`) vive dentro da camada de dados. |
| 6 | HIGH | Estado global mutável: conexão única compartilhada entre threads | `database.py:4-5, 8, 10` (`check_same_thread=False`) | Condição de corrida sob concorrência; impede injeção de dependência e testes. |
| 7 | HIGH | Regra de negócio e efeitos colaterais dentro dos controllers | `controllers.py:208-210, 247-250` (notificações), `controllers.py:264-292` (SQL direto no health) | Controller deveria só orquestrar; aqui ele notifica e consulta o banco. |
| 8 | HIGH | Debug ligado e bind em `0.0.0.0` | `app.py:8, 88` | Debugger do Werkzeug permite execução remota de código. |
| 9 | MEDIUM | Queries N+1 (pedido → itens → produto) | `models.py:171-201`, `models.py:203-233` | 1 + N + N×M queries por listagem. |
| 10 | MEDIUM | Pedido criado sem transação/rollback | `models.py:133-169` | Falha no meio deixa pedido sem itens ou estoque inconsistente. |
| 11 | MEDIUM | Validação duplicada e sem checagem de tipo | `controllers.py:28-54` vs `72-90`; `controllers.py:169-171`, `239-240` (`dados` pode ser `None`) | Regras divergem entre criar/atualizar; payload inválido vira 500. |
| 12 | MEDIUM | Tratamento de erro repetido em todo handler, vazando `str(e)` | `controllers.py:10-12` e demais blocos `except` | Sem handler central; detalhes internos expostos ao cliente. |
| 13 | MEDIUM | Schema + seed dentro do getter de conexão | `database.py:7-86` | Mistura infraestrutura, migração e dados de teste. |
| 14 | LOW | `print` como log | `controllers.py:8, 57, 106, 208-210`; `app.py:56, 83-86` | Sem nível, sem formato, loga e-mail de usuário. |
| 15 | LOW | Magic numbers / listas soltas | `models.py:257-262`; `controllers.py:47-52, 242` | Regras de negócio sem nome nem ponto único de alteração. |
| 16 | LOW | Imports não usados e `id` sombreando builtin | `models.py:2`, `database.py:2`; `models.py:24`, `controllers.py:14, 56` | Ruído e risco de bug sutil. |

### Projeto 2 — ecommerce-api-legacy (Node.js / Express 4 / sqlite3 em memória)

Domínio: LMS com checkout (usuários, cursos, matrículas, pagamentos, auditoria). 3 arquivos, ~180 linhas.

| # | Sev. | Problema | Arquivo:linha | Por que importa |
|---|------|----------|---------------|-----------------|
| 1 | CRITICAL | Credenciais de produção hardcoded | `src/utils.js:1-7` (`dbPass` l.3, `paymentGatewayKey` l.4) | Chave "live" do gateway e senha do banco no repositório. |
| 2 | CRITICAL | God Class: banco, schema, seed, rotas, regra de negócio e pagamento na mesma classe | `src/AppManager.js:4-139` | Nenhuma separação de camadas; nada é testável isoladamente. |
| 3 | CRITICAL | Número do cartão e chave do gateway impressos em log | `src/AppManager.js:45` | Vazamento de dado de cartão (PCI) e de segredo. |
| 4 | CRITICAL | "Criptografia" de senha falsa + senha padrão | `src/utils.js:17-23`, `src/AppManager.js:68` | Base64 truncado é reversível/colide; sem senha o usuário recebe `123456`. |
| 5 | HIGH | Rotas administrativas e destrutivas sem autenticação | `src/AppManager.js:80`, `131` | Relatório financeiro e exclusão de usuário abertos. |
| 6 | HIGH | Callback hell com regra de negócio dentro do handler | `src/AppManager.js:28-78` | 6 níveis de aninhamento; fluxo de checkout ilegível e sem reuso. |
| 7 | HIGH | Estado global mutável | `src/utils.js:9-10`, export em `25` | Cache sem limite (leak); `totalRevenue` exportado por valor, nunca atualiza. |
| 8 | HIGH | Checkout sem transação; delete deixa órfãos | `src/AppManager.js:50-62`, `131-137` | Matrícula sem pagamento se um insert falhar; matrículas/pagamentos órfãos. |
| 9 | MEDIUM | Queries N+1 no relatório financeiro | `src/AppManager.js:89-128` | 1 + cursos + 2×matrículas queries, coordenadas por contadores manuais. |
| 10 | MEDIUM | Erros ignorados nos callbacks | `src/AppManager.js:57, 92-93, 104, 106, 133` | `enrollments.length` quebra o processo se `err`; delete responde sucesso mesmo com erro. |
| 11 | MEDIUM | Validação de entrada ausente | `src/AppManager.js:29-35` | Só checa presença; e-mail, cartão e id sem formato/tipo. |
| 12 | MEDIUM | Respostas inconsistentes (texto vs JSON) | `src/AppManager.js:35, 38, 60, 135` | Cliente não consegue tratar erro de forma uniforme. |
| 13 | LOW | Nomes crípticos | `src/AppManager.js:29-33` (`u`, `e`, `p`, `cid`, `cc`) | Exige ler o fluxo inteiro para entender cada variável. |
| 14 | LOW | Magic strings/números | `src/AppManager.js:46` (`"4"`, `PAID`, `DENIED`), `src/utils.js:19` (`10000`) | Regra de aprovação e status espalhados como literais. |
| 15 | LOW | Import não usado, `self = this` misturado com arrow functions, `console.log` como log | `src/AppManager.js:2, 26`; `src/app.js:13` | Ruído e inconsistência de estilo. |

### Projeto 3 — task-manager-api (Python / Flask 3.0 / Flask-SQLAlchemy)

Domínio: gerenciador de tarefas (tasks, users, categories, relatórios). Já tem `models/`, `routes/`, `services/`, `utils/`. 15 arquivos, ~1.160 linhas.

| # | Sev. | Problema | Arquivo:linha | Por que importa |
|---|------|----------|---------------|-----------------|
| 1 | CRITICAL | Segredos hardcoded | `app.py:13`, `services/notification_service.py:7-10` | `SECRET_KEY` e senha SMTP versionadas. |
| 2 | CRITICAL | Senha com MD5 sem salt | `models/user.py:29, 32` | MD5 é quebrável por rainbow table em segundos. |
| 3 | CRITICAL | Hash da senha exposto na API | `models/user.py:21`; usado em `routes/user_routes.py:33, 85, 129, 209` | `to_dict()` inclui `password` em GET/POST/PUT/login. |
| 4 | CRITICAL | Autenticação falsa e nenhuma autorização | `routes/user_routes.py:210` (`fake-jwt-token-`), `52, 71-72` (role livre no cadastro) | Token previsível, nenhum endpoint protegido, qualquer um se cadastra como `admin`. |
| 5 | HIGH | Fat routes: validação, regra de negócio, persistência e serialização no handler; sem camada de controller | `routes/task_routes.py:11-63, 85-154, 156-223`; `routes/report_routes.py:12-101` | A separação em pastas existe, mas a responsabilidade não foi separada. |
| 6 | HIGH | CRUD de categorias dentro do blueprint de relatórios | `routes/report_routes.py:157-223` | Módulo com responsabilidade errada; difícil localizar e evoluir. |
| 7 | HIGH | Camadas mortas: service e helper nunca usados enquanto as rotas duplicam a lógica | `services/notification_service.py:4-48`; `utils/helpers.py:57-108` | Arquitetura "de fachada": a abstração existe e é ignorada. |
| 8 | HIGH | Debug ligado e bind em `0.0.0.0` | `app.py:34` | Mesmo risco de RCE do projeto 1. |
| 9 | MEDIUM | Queries N+1 | `routes/task_routes.py:41-57`; `routes/report_routes.py:53-68, 159-165`; `routes/user_routes.py:22` | Uma query por task/usuário/categoria a cada listagem. |
| 10 | MEDIUM | Regra de "atrasada" duplicada 6× (e já existe `Task.is_overdue`) | `routes/task_routes.py:30-39, 71-80, 283-287`; `routes/user_routes.py:171-180`; `routes/report_routes.py:33-43, 132-135`; original em `models/task.py:50-60` | Alterar a regra exige mexer em 6 lugares. |
| 11 | MEDIUM | APIs deprecated: `datetime.utcnow()` e `Query.get()` | `models/task.py:15-16, 52`; `models/user.py:14`; `models/category.py:11`; `routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227`; `routes/report_routes.py:105, 192, 213` | `utcnow` deprecated no Python 3.12; `Query.get` é legacy no SQLAlchemy 2.x (usar `db.session.get`). |
| 12 | MEDIUM | `except:` genérico engolindo erros | `routes/task_routes.py:62, 137, 204, 236`; `routes/user_routes.py:130, 149`; `routes/report_routes.py:186, 207, 221`; `utils/helpers.py:46, 49, 88` | Esconde a causa real e captura até `KeyboardInterrupt`. |
| 13 | MEDIUM | Validação incompleta | `routes/task_routes.py:113, 182` (prioridade sem checar tipo → 500); `routes/report_routes.py:196-197` (`data` pode ser `None`) | Payload inválido derruba o handler. |
| 14 | MEDIUM | Config no entry point; `python-dotenv` instalado e não usado | `app.py:11-13`, `requirements.txt:6` | Impossível trocar de ambiente sem editar código. |
| 15 | LOW | Imports e dependências não usados | `app.py:7`; `routes/task_routes.py:7`; `routes/user_routes.py:6`; `routes/report_routes.py:7-8`; `utils/helpers.py:3-7`; `models/task.py:3`; `requirements.txt` (`marshmallow`, `requests`) | Ruído e superfície de dependência desnecessária. |
| 16 | LOW | Magic numbers/strings repetidos apesar de constantes existirem | `routes/task_routes.py:110, 177`; `routes/user_routes.py:64, 71, 115`; `models/task.py:39`; constantes ignoradas em `utils/helpers.py:110-116` | Listas de status/roles divergem com o tempo. |
| 17 | LOW | `print` como log e booleanos verbosos | `routes/task_routes.py:149, 153, 219, 234`; `routes/user_routes.py:83, 89, 147`; `models/task.py:38-43`; `models/user.py:34-38` | Legibilidade. |

### Padrões recorrentes (insumo para o catálogo da skill)

| Padrão | P1 | P2 | P3 |
|--------|----|----|----|
| Segredos hardcoded | ✓ | ✓ | ✓ |
| Senha fraca / exposta | ✓ | ✓ | ✓ |
| SQL Injection / SQL arbitrário | ✓ | – | – |
| God class / god module | ✓ | ✓ | – |
| Lógica de negócio em controller/rota | ✓ | ✓ | ✓ |
| Estado global mutável | ✓ | ✓ | – |
| Endpoints sensíveis sem auth | ✓ | ✓ | ✓ |
| Debug em produção | ✓ | – | ✓ |
| N+1 | ✓ | ✓ | ✓ |
| Sem transação | ✓ | ✓ | – |
| Erro engolido / sem handler central | ✓ | ✓ | ✓ |
| Validação ausente ou duplicada | ✓ | ✓ | ✓ |
| APIs deprecated | – | – | ✓ |
| Magic numbers, nomes ruins, `print`/`console.log`, imports mortos | ✓ | ✓ | ✓ |

---

## B) Construção da Skill

### Estrutura

```
.claude/skills/refactor-arch/
├── SKILL.md                          # o prompt: 3 fases, regras invioláveis, formatos de saída
└── references/
    ├── project-analysis.md           # heurísticas de detecção (Fase 1)
    ├── anti-patterns-catalog.md      # 23 anti-patterns com sinais e severidade (Fase 2)
    ├── audit-report-template.md      # formato do relatório (Fase 2)
    ├── mvc-guidelines.md             # arquitetura alvo e adaptação por nível (Fase 3)
    └── refactoring-playbook.md       # 17 transformações com antes/depois (Fase 3)
```

| Área de conhecimento exigida | Arquivo |
|---|---|
| Análise de projeto | `references/project-analysis.md` |
| Catálogo de anti-patterns | `references/anti-patterns-catalog.md` |
| Template de relatório | `references/audit-report-template.md` |
| Guidelines de arquitetura | `references/mvc-guidelines.md` |
| Playbook de refatoração | `references/refactoring-playbook.md` |

### Decisões de design

1. **`SKILL.md` é só orquestração; o conhecimento fica nas referências.** O `SKILL.md` diz o que fazer, em que ordem e em que formato imprimir. Cada referência é lida no momento em que a fase precisa dela (tabela "quando ler"), o que mantém o contexto enxuto.
2. **Regras invioláveis no topo.** Nove regras curtas que valem para as três fases: Fases 1–2 somente leitura, confirmação como portão real, todo finding com evidência, contrato preservado, nenhum ✓ sem execução, agnosticismo, sem dependências novas desnecessárias, sem commits, idioma.
3. **A confirmação encerra o turno.** A Fase 2 termina imprimindo `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` e a skill é instruída a não chamar nenhuma ferramenta depois disso. Só `y/yes/s/sim` prossegue. Em execução não interativa, a skill para na Fase 2 — foi assim que ensaiei as Fases 1–2 (`claude -p`) antes de liberar a Fase 3.
4. **Evidência verificável.** Linha de finding vem de leitura real do arquivo; "linha aproximada" ou "vários arquivos" são proibidos pelo template. Conferi os três relatórios com um script: 414 referências `arquivo:linha`, todas apontando para arquivos existentes e dentro do tamanho do arquivo.
5. **Inventário de rotas como contrato.** A Fase 1 lista método, caminho, handler e classe de risco (`read`, `write`, `destructive`) de cada rota. A Fase 3 captura uma linha de base antes de alterar o código e compara depois.
6. **Intervenção proporcional ao nível de organização.** A Fase 1 classifica o projeto em N0 (monolito sem camadas), N1 (camadas por arquivo único) ou N2 (parcialmente em camadas). Em N2 a regra é manter o que está certo, criar só a camada que falta e passar a usar (ou remover) camadas mortas.
7. **Catálogo e playbook ligados por ID.** Cada anti-pattern (`AP-xx`) aponta para a transformação que o resolve (`T-xx`); o relatório cita os dois, e o resumo da Fase 3 informa `resolved` ou `deferred` por finding.
8. **Honestidade sobre o que não foi resolvido.** Correções que mudariam o contrato (autenticação em todas as rotas, padronizar formato de erro) ficam como `deferred` com motivo, em vez de "zero anti-patterns restantes".

### Anti-patterns do catálogo e por quê

Os 23 padrões vieram da análise manual: entrou no catálogo o que apareceu em pelo menos um projeto, descrito por **sinal de detecção** concreto (o que procurar), não por adjetivo.

| ID | Anti-pattern | Sev. | Por que está no catálogo |
|---|---|---|---|
| AP-01 | Credenciais e segredos hardcoded | CRITICAL | Presente nos 3 projetos |
| AP-02 | Injeção (SQL, comando, execução arbitrária) | CRITICAL | Todo o `models.py` do projeto 1 e o `/admin/query` |
| AP-03 | Armazenamento inseguro de senha | CRITICAL | Texto puro (P1), base64 truncado (P2), MD5 (P3) |
| AP-04 | Exposição de dados sensíveis | CRITICAL | Senha em resposta (P1, P3), cartão em log (P2), secret no `/health` (P1) |
| AP-05 | God Class / Module / Method | CRITICAL | `AppManager` (P2), `models.py` (P1) |
| AP-06 | Controle de acesso ausente ou falso | CRITICAL | Rotas admin abertas, token falso, `role` autoatribuído |
| AP-07 | Regra de negócio ou acesso a dados no controller/rota | HIGH | Presente nos 3 projetos |
| AP-08 | Camada ausente, morta ou com responsabilidade trocada | HIGH | Necessário para o projeto 3: pastas existem, arquitetura não |
| AP-09 | Estado global mutável / sem injeção de dependência | HIGH | Conexão global (P1), cache e acumulador globais (P2) |
| AP-10 | Configuração insegura de execução | HIGH | `debug=True` + `0.0.0.0` (P1, P3) |
| AP-11 | Escrita em várias etapas sem transação | HIGH | Pedido (P1), checkout e delete com órfãos (P2) |
| AP-12 | Queries N+1 | MEDIUM | Presente nos 3 projetos |
| AP-13 | Validação ausente ou duplicada | MEDIUM | Presente nos 3 projetos |
| AP-14 | Tratamento de erro ausente, genérico ou repetido | MEDIUM | `try/except` copiado (P1), `err` ignorado (P2), `except:` (P3) |
| AP-15 | **APIs deprecated** | MEDIUM | Exigência do desafio; tabela obsoleto → moderno por stack |
| AP-16 | Código duplicado | MEDIUM | Regra de "atrasada" repetida 6× (P3), serialização (P1) |
| AP-17 | Infraestrutura misturada | MEDIUM | Schema e seed dentro do getter de conexão (P1, P2) |
| AP-18 | Callback hell | MEDIUM | Checkout e relatório do projeto 2 |
| AP-19 | Contrato de resposta inconsistente | MEDIUM | Texto vs JSON (P2), formatos de erro diferentes (P1) |
| AP-20 | Números e strings mágicos | LOW | Presente nos 3 projetos |
| AP-21 | Nomenclatura ruim | LOW | `u`, `e`, `p`, `cc` (P2); `id` sombreando builtin (P1) |
| AP-22 | Log por `print`/`console.log` | LOW | Presente nos 3 projetos |
| AP-23 | Código morto, imports e dependências não usados | LOW | Presente nos 3 projetos |

Distribuição: 6 CRITICAL, 5 HIGH, 8 MEDIUM, 4 LOW. Problemas reais fora do catálogo são reportados com `AP-00` (ex.: no projeto 1 a skill encontrou que quantidade negativa em pedido aumenta o estoque).

### Como a skill é agnóstica de tecnologia

- **Detecção por evidência, não por suposição:** linguagem e versões vêm do manifesto (`requirements.txt`, `package.json`, `pom.xml`, `go.mod`...); framework é confirmado pela assinatura no código. As tabelas cobrem Python, Node, Java, Go, PHP, Ruby e C#.
- **Sinais descrevem comportamento:** "query montada por concatenação com valor externo", "chamada ao banco dentro de laço". Os trechos de busca são atalhos por linguagem, não a definição do padrão.
- **Exemplos são ilustração:** o playbook mostra antes/depois em Python e JavaScript e instrui a aplicar o mesmo movimento no idioma do stack detectado.
- **Estrutura alvo relativa ao projeto:** as camadas são criadas na raiz de código existente (`src/` no Express, raiz no Flask), com os nomes e convenções que o projeto já usa.
- **Validação escolhida por stack:** cliente de teste em processo quando o framework oferece; servidor real em porta local caso contrário.
- **Nada específico dos três projetos** aparece na skill: ela foi copiada sem alteração entre eles.

### Desafios encontrados e como resolvi

| # | Problema | Onde apareceu | Correção na skill |
|---|---|---|---|
| 1 | A estrutura proposta no relatório (`views/routes.py`) não era a mesma executada na Fase 3 (`routes/`) | Projeto 1 | As guidelines de MVC passaram a ser lidas **antes** de propor a estrutura na Fase 2, e o `SKILL.md` exige que a proposta seja a que a Fase 3 executa |
| 2 | A guarda de rotas administrativas deixou 2 das 3 rotas respondendo **403** no boot padrão (`npm start` sem variáveis) | Projeto 2 | Nova regra inviolável: com o boot padrão, toda rota não `destructive` responde como antes. O T-06 ganhou duas políticas: rotas destrutivas ficam desligadas sem `ADMIN_TOKEN`; as demais só exigem o token quando ele está configurado. A validação passou a rodar primeiro com o boot padrão |
| 3 | Saída em inglês em um projeto e em português em outro | Ensaio no projeto 2 | Regra de idioma: pt-BR por padrão, rótulos fixos em inglês |
| 4 | Risco de a Fase 3 "validar" sem executar | Desenho | Regra "nenhum ✓ sem execução" e tabela `Baseline × After` por rota no resumo final |

O projeto 2 passou por **duas execuções**: a primeira gerou o código MVC e o relatório do legado (`reports/audit-project-2.md`); depois do ajuste nº 2, a skill foi executada de novo sobre o resultado, apontou o 403 do boot padrão como finding crítico e o corrigiu (`reports/audit-project-2-iteracao-2.md`). O projeto 3 já rodou com a versão final.

---

## C) Resultados

### Resumo dos relatórios

| Relatório | Projeto | Arquivos | Total | CRITICAL | HIGH | MEDIUM | LOW | APIs deprecated |
|---|---|---|---|---|---|---|---|---|
| [`reports/audit-project-1.md`](reports/audit-project-1.md) | code-smells-project | 4 (~780 linhas) | 22 | 7 | 5 | 6 | 4 | Nenhuma (verificado contra Flask 3.1.1) |
| [`reports/audit-project-2.md`](reports/audit-project-2.md) | ecommerce-api-legacy | 3 (~180 linhas) | 21 | 5 | 5 | 7 | 4 | Nenhuma (verificado contra Express 4.18 e Node) |
| [`reports/audit-project-3.md`](reports/audit-project-3.md) | task-manager-api | 15 (~1158 linhas) | 19 | 4 | 4 | 7 | 4 | `datetime.utcnow()` e `Query.get()` |

Todos os problemas da análise manual foram encontrados pela skill nos três projetos (o mínimo exigido era 5).

### Antes e depois

**Projeto 1 — code-smells-project** (N1: camadas por arquivo único)

```
ANTES                         DEPOIS
app.py                        app.py                 composition root (create_app)
controllers.py                .env.example
models.py                     config/settings.py
database.py                   database/              connection · schema · seed
requirements.txt              models/                produto · usuario · pedido · relatorio · sistema · errors
                              services/              pedido_service · notificacao_service
                              validators/            produto · usuario · pedido · admin
                              controllers/           produto · usuario · pedido · relatorio · sistema
                              routes/                um Blueprint por recurso
                              middlewares/           error_handler · auth
```

**Projeto 2 — ecommerce-api-legacy** (N0: monolito sem camadas)

```
ANTES                         DEPOIS
src/app.js                    src/app.js             composition root + listen
src/AppManager.js             src/config/            leitura do ambiente
src/utils.js                  src/database/          connection (Promises + transação) · schema · seed
                              src/models/            user · course · enrollment · payment · auditLog
                              src/services/          checkout · financialReport · paymentGateway
                              src/controllers/       checkout · admin · user
                              src/validators/        checkout · user · common
                              src/routes/            express.Router por recurso
                              src/middlewares/       errorHandler · adminAuth
                              src/utils/             logger · password (scrypt) · errors
                              .env.example
```

**Projeto 3 — task-manager-api** (N2: parcialmente em camadas)

```
ANTES                         DEPOIS
app.py                        app.py                 composition root (create_app)
database.py                   config/settings.py     NOVO
seed.py                       database/              connection · schema · seed (era database.py)
models/   task user category  models/                MANTIDO + regras de domínio, consultas, errors.py
routes/   task user report    controllers/           NOVO: task · user · category · report · health
services/ notification (morto) routes/               MANTIDO, só mapeamento; category_routes e health_routes separados
utils/    helpers (morto)     services/              report_service · auth_service (notification removido)
                              middlewares/           NOVO: error_handler · auth
                              utils/helpers.py       enxuto, agora usado
                              seed.py · .env.example
```

No projeto 3 a skill **não** recriou o que já estava certo: manteve `models/` e `routes/`, criou a camada que faltava (`controllers/`), tirou o CRUD de categorias de dentro de `report_routes.py` e removeu o service morto.

### Mudanças intencionais de contrato

| Projeto | Mudança | Motivo |
|---|---|---|
| 1 | `senha` não é mais devolvida em `/usuarios` e `/usuarios/<id>` | Exposição de credencial |
| 1 | `/health` não devolve mais `secret_key`, `debug` e `db_path` | Exposição de segredo |
| 1 | `/admin/reset-db` e `/admin/query` respondem 403 sem `ADMIN_TOKEN` (401 com token errado) | Rotas destrutivas |
| 1 | `tipo` enviado no cadastro é ignorado (sempre `cliente`) | Privilégio autoatribuído |
| 2 | Com `ADMIN_TOKEN` definido, relatório financeiro e delete de usuário exigem `X-Admin-Token` | Controle de acesso opcional |
| 2 | `DELETE /api/users/:id` remove também matrículas e pagamentos do usuário | Órfãos no banco |
| 3 | `password` não é mais devolvido em nenhuma resposta de usuário | Exposição do hash |
| 3 | `role` enviado em `POST/PUT /users` é ignorado sem credencial de admin | Privilégio autoatribuído |
| 3 | Token de login passa a ser assinado, no lugar de `fake-jwt-token-<id>` | Token previsível |
| 1, 2, 3 | Erros 500 devolvem mensagem genérica; o detalhe vai para o log | Vazamento de detalhes internos |

Com o boot padrão, todas as rotas originais dos três projetos respondem com o mesmo status de antes, exceto as duas rotas destrutivas do projeto 1.

### Checklist de validação

| Item | Projeto 1 | Projeto 2 | Projeto 3 |
|---|---|---|---|
| **Fase 1** — Linguagem detectada corretamente | ✅ Python | ✅ JavaScript (Node.js) | ✅ Python |
| Framework detectado corretamente | ✅ Flask 3.1.1 | ✅ Express 4.18 | ✅ Flask 3.0.0 |
| Domínio descrito corretamente | ✅ E-commerce | ✅ LMS com checkout | ✅ Task Manager |
| Número de arquivos condiz com a realidade | ✅ 4 | ✅ 3 | ✅ 15 |
| **Fase 2** — Relatório segue o template | ✅ | ✅ | ✅ |
| Cada finding tem arquivo e linhas exatos | ✅ 149 refs | ✅ 68 refs | ✅ 197 refs |
| Findings ordenados CRITICAL → LOW | ✅ | ✅ | ✅ |
| Mínimo de 5 findings | ✅ 22 | ✅ 21 | ✅ 19 |
| Pelo menos 1 CRITICAL ou HIGH | ✅ 12 | ✅ 10 | ✅ 8 |
| Detecção de APIs deprecated (se aplicável) | ✅ verificado, nenhuma | ✅ verificado, nenhuma | ✅ 2 APIs |
| Pausa e pede confirmação antes da Fase 3 | ✅ | ✅ | ✅ |
| **Fase 3** — Estrutura segue o padrão MVC | ✅ | ✅ | ✅ |
| Configuração em módulo próprio, sem hardcoded | ✅ `config/settings.py` | ✅ `src/config/` | ✅ `config/settings.py` |
| Models abstraem os dados | ✅ | ✅ | ✅ |
| Views/Routes separadas | ✅ `routes/` | ✅ `src/routes/` | ✅ `routes/` |
| Controllers concentram o fluxo | ✅ | ✅ | ✅ |
| Error handling centralizado | ✅ | ✅ | ✅ |
| Entry point claro | ✅ `app.py` | ✅ `src/app.js` | ✅ `app.py` |
| Aplicação inicia sem erros | ✅ | ✅ | ✅ |
| Endpoints originais respondem corretamente | ✅ 28/28 | ✅ 13/13 | ✅ 30/30 |

### Logs das aplicações rodando após a refatoração

Além da validação que a própria skill executa na Fase 3, cada projeto foi conferido com um script de smoke independente (fora do Claude Code): boot pelo comando real e uma requisição por rota e por cenário de erro.

<details>
<summary><b>Projeto 1</b> — <code>python app.py</code> + 28 requisições</summary>

```
INFO __main__: Servidor iniciado em http://0.0.0.0:5055
 * Serving Flask app 'app'
 * Debug mode: off

GET     /                                        exp=200 got=200 OK
GET     /produtos                                exp=200 got=200 OK
GET     /produtos/busca?q=mouse&preco_min=10     exp=200 got=200 OK
GET     /produtos/1                              exp=200 got=200 OK
GET     /produtos/9999                           exp=404 got=404 OK
POST    /produtos                                exp=201 got=201 OK
POST    /produtos                                exp=400 got=400 OK
PUT     /produtos/11                             exp=200 got=200 OK
DELETE  /produtos/11                             exp=200 got=200 OK
GET     /usuarios                                exp=200 got=200 OK
GET     /usuarios/1                              exp=200 got=200 OK
POST    /usuarios                                exp=201 got=201 OK
POST    /login                                   exp=200 got=200 OK
POST    /login                                   exp=200 got=200 OK
POST    /login   (senha: ' OR '1'='1)            exp=401 got=401 OK
POST    /login   (email: ' OR '1'='1' --)        exp=401 got=401 OK
POST    /pedidos                                 exp=201 got=201 OK
POST    /pedidos (estoque insuficiente)          exp=400 got=400 OK
GET     /pedidos                                 exp=200 got=200 OK
GET     /pedidos/usuario/2                       exp=200 got=200 OK
PUT     /pedidos/1/status                        exp=200 got=200 OK
PUT     /pedidos/1/status (status inválido)      exp=400 got=400 OK
GET     /relatorios/vendas                       exp=200 got=200 OK
GET     /health                                  exp=200 got=200 OK
POST    /admin/query    (sem token)              exp=401 got=401 OK
POST    /admin/reset-db (sem token)              exp=401 got=401 OK
POST    /admin/query    (com X-Admin-Token)      exp=200 got=200 OK
GET     /nao-existe                              exp=404 got=404 OK
FAILS: 0 / 28

senha exposta em /usuarios: False
health keys: ['ambiente', 'counts', 'database', 'status', 'versao']
senhas no banco: ['scrypt:32768:8:1$KdVWuTh8', 'scrypt:32768:8:1$TKxr4Q2p', ...]
```
</details>

<details>
<summary><b>Projeto 2</b> — <code>npm start</code> com e sem <code>ADMIN_TOKEN</code></summary>

```
=== sem ADMIN_TOKEN (boot padrão: npm start)
[WARN] PAYMENT_GATEWAY_KEY não definida; usando valor efêmero
[WARN] ADMIN_TOKEN não definida; rotas administrativas abertas sem X-Admin-Token
[INFO] LMS API rodando na porta 3102
POST   /api/checkout                      exp=200 got=200 OK  {"msg":"Sucesso","enrollment_id":2}
GET    /api/admin/financial-report        exp=200 got=200 OK  [{"course":"Clean Architecture","revenue":997,...
DELETE /api/users/1                       exp=200 got=200 OK  Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.
FAILS 0 / 3

=== com ADMIN_TOKEN
[INFO] LMS API rodando na porta 3101
[INFO] Cobrança de 497 no cartão ****4444: PAID
POST   /api/checkout                      exp=200 got=200 OK  {"msg":"Sucesso","enrollment_id":2}
POST   /api/checkout                      exp=200 got=200 OK  {"msg":"Sucesso","enrollment_id":3}
POST   /api/checkout (cartão 5...)        exp=400 got=400 OK  Pagamento recusado
POST   /api/checkout (campos ausentes)    exp=400 got=400 OK  Bad Request
POST   /api/checkout (curso 99)           exp=404 got=404 OK  Curso não encontrado
GET    /api/admin/financial-report        exp=200 got=200 OK  (com X-Admin-Token)
GET    /api/admin/financial-report        exp=401 got=401 OK  Não autorizado
DELETE /api/users/1                       exp=401 got=401 OK  Não autorizado
DELETE /api/users/1                       exp=200 got=200 OK  (com X-Admin-Token)
GET    /api/admin/financial-report        exp=200 got=200 OK  (sem aluno "Unknown" após o delete)
FAILS 0 / 10
```
</details>

<details>
<summary><b>Projeto 3</b> — <code>python seed.py</code> + <code>python app.py</code> + 30 requisições</summary>

```
Seed concluído com sucesso!
  3 usuários
  4 categorias
  10 tasks
 * Debug mode: off
health=200 tasks=200 summary=200

GET     /                                          exp=200 got=200 OK
GET     /health                                    exp=200 got=200 OK
GET     /tasks                                     exp=200 got=200 OK
GET     /tasks/1                                   exp=200 got=200 OK
GET     /tasks/999                                 exp=404 got=404 OK
POST    /tasks                                     exp=201 got=201 OK
POST    /tasks (título curto)                      exp=400 got=400 OK
POST    /tasks (status inválido)                   exp=400 got=400 OK
POST    /tasks (prioridade "alta")                 exp=400 got=400 OK
PUT     /tasks/11                                  exp=200 got=200 OK
GET     /tasks/search?q=login&status=in_progress   exp=200 got=200 OK
GET     /tasks/stats                               exp=200 got=200 OK
DELETE  /tasks/11                                  exp=200 got=200 OK
GET     /users                                     exp=200 got=200 OK
GET     /users/1                                   exp=200 got=200 OK
POST    /users                                     exp=201 got=201 OK
POST    /users (e-mail repetido)                   exp=409 got=409 OK
POST    /users (e-mail inválido)                   exp=400 got=400 OK
PUT     /users/4                                   exp=200 got=200 OK
GET     /users/1/tasks                             exp=200 got=200 OK
POST    /login                                     exp=200 got=200 OK
POST    /login (senha errada)                      exp=401 got=401 OK
DELETE  /users/4                                   exp=200 got=200 OK
GET     /reports/summary                           exp=200 got=200 OK
GET     /reports/user/1                            exp=200 got=200 OK
GET     /categories                                exp=200 got=200 OK
POST    /categories                                exp=201 got=201 OK
PUT     /categories/5                              exp=200 got=200 OK
DELETE  /categories/5                              exp=200 got=200 OK
GET     /nao-existe                                exp=404 got=404 OK
FAILS: 0 / 30

password em respostas: False False False
role do novo usuario (pediu admin): user
hashes: ['scrypt:32768:8:1$SUOOS', 'scrypt:32768:8:1$H8wGO']
```

O script roda com `DeprecationWarning` tratado como erro: nenhuma API deprecated é mais chamada. Com `ADMIN_TOKEN` definido, `/reports/*` e `DELETE /users/<id>` respondem 401 sem o header e 200 com ele (33/33).
</details>

### Como a skill se comportou em stacks diferentes

- **Python/Flask com SQL puro (projeto 1):** classificado como N1. A maior parte do trabalho foi decompor `models.py` por domínio e parametrizar as queries. A validação usou o cliente de teste do Flask, sem abrir porta.
- **Node.js/Express (projeto 2):** classificado como N0. Além de separar camadas, a skill precisou trocar o estilo de callbacks por `async/await` (adaptador de Promises sobre o `sqlite3`) e criar um wrapper para o Express 4 propagar erros assíncronos. Usou só `crypto` nativo para hash de senha — nenhuma dependência nova. Foi o projeto que expôs a falha da guarda administrativa (desafio nº 2).
- **Python/Flask já organizado (projeto 3):** classificado como N2. A skill não refez o que estava certo. O valor veio de `AP-08` (camada ausente, morta ou trocada): criou `controllers/`, removeu o service morto, passou a usar `Task.is_overdue()` no lugar das 6 cópias e substituiu as APIs deprecated. Foi o único com APIs deprecated de fato.
- **Em comum:** os mesmos 23 padrões e 17 transformações serviram aos três; o que mudou foi o idioma da solução (Blueprint × Router, `werkzeug.security` × `crypto.scrypt`, `errorhandler` × middleware de erro).

---

## D) Como Executar

### Pré-requisitos

- [Claude Code](https://docs.claude.com/en/docs/claude-code/overview) instalado e autenticado
- Python 3.10+ (projetos 1 e 3) e Node.js 18+ (projeto 2)
- Git

### Executar a skill

```bash
# Projeto 1
cd code-smells-project
claude "/refactor-arch"

# Projeto 2
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3
cd ../task-manager-api
claude "/refactor-arch"
```

Em cada execução:

1. A skill imprime `PHASE 1: PROJECT ANALYSIS` e o `ARCHITECTURE AUDIT REPORT`.
2. Ela para em `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`. Nenhum arquivo foi alterado até aqui.
3. Respondendo `y`, o relatório é salvo em `reports/audit-report.md` dentro do projeto e a Fase 3 é executada. Para escolher o destino: `claude "/refactor-arch ../reports/audit-project-1.md"`.
4. Ao final a skill imprime `PHASE 3: REFACTORING COMPLETE` com a nova estrutura, o status de cada finding e a tabela de validação por rota.

Os projetos deste repositório já estão refatorados. Para rodar a skill sobre o código original:

```bash
git checkout 6d1ce62 -- code-smells-project/app.py code-smells-project/controllers.py code-smells-project/models.py code-smells-project/database.py
```

### Validar que a refatoração funcionou

```bash
# Projeto 1 — http://localhost:5000
cd code-smells-project
pip install -r requirements.txt
python app.py
curl http://localhost:5000/health
curl http://localhost:5000/produtos

# Projeto 2 — http://localhost:3000 (requisições de exemplo em api.http)
cd ecommerce-api-legacy
npm install
npm start
curl http://localhost:3000/api/admin/financial-report

# Projeto 3 — http://localhost:5000
cd task-manager-api
pip install -r requirements.txt
python seed.py
python app.py
curl http://localhost:5000/tasks
curl http://localhost:5000/reports/summary
```

Nenhuma variável de ambiente é obrigatória em desenvolvimento. Cada projeto tem um `.env.example` com as variáveis disponíveis (`SECRET_KEY`, `ADMIN_TOKEN`, `DEBUG`, porta, banco).

### Reutilizar a skill em outro projeto

```bash
cp -r code-smells-project/.claude/skills/refactor-arch <seu-projeto>/.claude/skills/
cd <seu-projeto>
claude "/refactor-arch"
```
