================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1 (SQLite / sqlite3 driver puro)
Files:   4 analyzed | ~780 lines of code
Date:    2026-10-06

## Summary
CRITICAL: 7 | HIGH: 5 | MEDIUM: 6 | LOW: 4

## Findings

### [CRITICAL] F-01 — Quantidade negativa em pedido manipula estoque e total
Pattern: AP-00
File: models.py:139-146, 163-166
File: controllers.py:195-201
Description: criar_pedido não valida o sinal nem o tipo de item["quantidade"]; `produto["estoque"] < item["quantidade"]` (144) passa com valor negativo, o total fica negativo (146) e `estoque = estoque - <negativo>` (164) aumenta o estoque. O controller só verifica se `itens` existe.
Impact: Qualquer cliente anônimo infla o estoque de qualquer produto e gera pedidos com total negativo, o que distorce o faturamento de /relatorios/vendas.
Recommendation: Validar cada item (produto_id inteiro, quantidade inteira > 0) antes de chamar o model (T-12).

### [CRITICAL] F-02 — Segredos hardcoded
Pattern: AP-01
File: app.py:7
File: controllers.py:289
Description: app.config["SECRET_KEY"] recebe o literal 'minh…123' no código, e o mesmo literal é repetido no corpo da resposta de health_check.
Impact: A chave de assinatura de sessão fica versionada e é publicada por um endpoint público, então qualquer cliente consegue forjar dados assinados pelo Flask.
Recommendation: Ler SECRET_KEY do ambiente num módulo de config, documentar em .env.example e removê-la da resposta (T-01).

### [CRITICAL] F-03 — Injeção de SQL nas queries do model
Pattern: AP-02
File: models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-151, 155, 157-161, 163-166, 174, 188, 192, 220, 224, 279-281, 289-299
Description: Todas as queries com parâmetro são montadas por concatenação de strings; login_usuario (109-111) coloca email e senha direto no WHERE, e buscar_produtos (289-297) concatena `termo` e `categoria` vindos da query string.
Impact: O login é burlável com `' OR '1'='1`, e /produtos/busca?q=... permite ler qualquer tabela (inclusive as senhas de usuarios) ou alterá-la.
Recommendation: Trocar todas as queries por versões parametrizadas com placeholders `?` (T-02).

### [CRITICAL] F-04 — Endpoint de execução de SQL arbitrário
Pattern: AP-02
File: app.py:59-78
Description: executar_query lê `sql` do corpo da requisição e o passa a cursor.execute(query), com commit para comandos que não são SELECT.
Impact: Qualquer cliente anônimo executa SELECT, UPDATE, DELETE ou DROP em qualquer tabela.
Recommendation: Proteger com guarda administrativa por token de ambiente e rejeitar comandos fora de SELECT (T-02, T-06).

### [CRITICAL] F-05 — Senhas em texto puro
Pattern: AP-03
File: models.py:109-111, 126-129
File: database.py:75-83
Description: criar_usuario grava `senha` exatamente como recebida, login_usuario compara a senha por igualdade no WHERE, e o seed insere senhas legíveis (ex.: 'admi…123' para o admin).
Impact: Um vazamento do banco, ou a injeção de F-03, entrega a senha real de todos os usuários.
Recommendation: Gravar hash com salt (PBKDF2 de hashlib ou werkzeug.security, que já vem com o Flask), verificar com comparação segura e gerar o hash também no seed (T-03).

### [CRITICAL] F-06 — Exposição de dados sensíveis
Pattern: AP-04
File: models.py:79-86, 95-102
File: controllers.py:276-290, 12, 22, 62, 96, 109, 126, 134, 144, 165, 186, 220, 227, 235, 255, 262, 292
File: app.py:78
Description: get_todos_usuarios e get_usuario_por_id serializam o campo "senha", que sai em GET /usuarios e GET /usuarios/<id>. health_check devolve db_path, debug e secret_key. Todos os handlers devolvem str(e) ao cliente.
Impact: Qualquer cliente lista as senhas de todos os usuários e a chave da aplicação; mensagens internas do SQLite revelam a estrutura do banco.
Recommendation: Remover senha dos serializadores, retirar configuração do health e devolver mensagem genérica no erro 500 (T-04).

### [CRITICAL] F-07 — Controle de acesso ausente
Pattern: AP-06
File: app.py:47-57, 59-78
File: controllers.py:128-134, 229-235, 237-255, 257-262
Description: /admin/reset-db apaga as quatro tabelas e /admin/query executa SQL sem nenhuma verificação de credencial. Também ficam abertos a qualquer cliente a lista de usuários, todos os pedidos, a troca de status de pedido e o relatório financeiro. Não há middleware nem decorator de autenticação no projeto, e /login não emite token.
Impact: Um único POST anônimo destrói o banco de dados inteiro.
Recommendation: Guarda administrativa (token via ambiente, 401/403) nas rotas /admin (T-06). Autenticar todas as rotas mudaria o contrato e fica como adiado.

### [HIGH] F-08 — God module de acesso a dados
Pattern: AP-05
File: models.py:1-314
Description: Um único módulo concentra o acesso a dados das 4 tabelas (produtos, usuarios, pedidos, itens_pedido), a regra de cálculo de pedido e estoque (133-169) e a regra de desconto do relatório (256-262).
Impact: Qualquer mudança em um domínio mexe no mesmo arquivo e não dá para testar os domínios isoladamente. A severidade foi rebaixada de CRITICAL pelo critério de desempate porque o dano é só de manutenção.
Recommendation: Separar um model por domínio e um service para a criação de pedido (T-05).

### [HIGH] F-09 — Acesso a dados e regra de negócio no controller/rota
Pattern: AP-07
File: controllers.py:3, 24-62, 52-54, 208-210, 247-250, 264-274
File: app.py:47-78
Description: health_check executa SQL diretamente via get_db. criar_produto tem 39 linhas e define inline a lista de categorias válidas. criar_pedido e atualizar_status_pedido disparam "notificações" (email/SMS/push) no handler. reset_database e executar_query fazem SQL dentro do entry point.
Impact: A regra fica espalhada entre camadas e não dá para reutilizá-la nem testá-la sem HTTP.
Recommendation: Controllers só leem a entrada, chamam um model/service e respondem; SQL fica nos models e notificações no service (T-07).

### [HIGH] F-10 — Conexão global mutável compartilhada entre threads
Pattern: AP-09
File: database.py:4-10
Description: `db_connection` é uma variável de módulo reatribuída via `global` e aberta com check_same_thread=False, e a mesma conexão serve todas as requisições.
Impact: Com o servidor multithread do Flask, transações de requisições diferentes se misturam: o commit de uma requisição grava escritas pela metade de outra.
Recommendation: Conexão por requisição (flask.g + teardown), com o caminho vindo da config (T-09).

### [HIGH] F-11 — Configuração insegura de execução
Pattern: AP-10
File: app.py:8, 9, 88
File: database.py:5
Description: DEBUG=True fixo, `CORS(app)` liberado para qualquer origem, `app.run(host="0.0.0.0", port=5000, debug=True)` e db_path "loja.db" fixos no código.
Impact: Debug com bind em todas as interfaces expõe o debugger do Werkzeug, que executa código na rede local, e não dá para mudar a configuração por ambiente.
Recommendation: Ler DEBUG, HOST, PORT, DB_PATH e CORS_ORIGINS do ambiente, com debug desligado por padrão (T-01).

### [HIGH] F-12 — Escrita em várias etapas sem transação
Pattern: AP-11
File: models.py:133-169, 65-70
File: app.py:51-55
Description: criar_pedido lê o estoque e depois faz INSERT em pedidos, INSERT em itens e UPDATE de estoque, com commit só no fim e sem rollback. deletar_produto remove o produto e deixa itens_pedido órfãos. reset_database faz 4 DELETEs sem rollback.
Impact: Uma exceção no meio deixa escritas pendentes na conexão global, que o próximo commit de qualquer requisição grava. A verificação de estoque não é atômica (venda acima do estoque).
Recommendation: Envolver cada operação composta em transação (`with conn:`) com rollback no erro (T-10).

### [MEDIUM] F-13 — Queries N+1
Pattern: AP-12
File: models.py:139-140, 154-155, 186-199, 219-231, 239-254
Description: criar_pedido consulta o produto duas vezes por item. get_pedidos_usuario e get_todos_pedidos fazem uma query de itens por pedido e uma de produto por item. relatorio_vendas faz 5 consultas separadas em pedidos que só mudam o filtro.
Impact: GET /pedidos cresce para 1 + P + I queries, com custo linear no volume de pedidos.
Recommendation: Usar JOIN de itens com produtos e agregação com SUM/COUNT CASE numa só query (T-11).

### [MEDIUM] F-14 — Validação de entrada ausente, duplicada e divergente
Pattern: AP-13
File: controllers.py:28-54, 72-90, 118-121, 157-158, 169-170, 239-240
File: app.py:61-62
Description: O bloco de validação de criar_produto está copiado em atualizar_produto, mas sem a checagem de tamanho de nome e de categoria (regras divergentes). `preco < 0` é comparado sem checar o tipo. float(preco_min) não é tratado. login, atualizar_status_pedido e executar_query chamam dados.get com dados possivelmente None. O formato do e-mail não é validado.
Impact: Entradas mal formadas viram 500 em vez de 400, e PUT aceita categoria inválida que POST rejeita.
Recommendation: Centralizar validadores por recurso e reaproveitá-los em criar e atualizar (T-12).

### [MEDIUM] F-15 — Tratamento de erro repetido e sem handler central
Pattern: AP-14
File: controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292
File: app.py:77-78
Description: Todo handler repete `try/except Exception as e: return jsonify({"erro": str(e)}), 500`, e não existe nenhum @app.errorhandler.
Impact: São 17 cópias do mesmo bloco, e nenhuma faz log estruturado nem rollback.
Recommendation: Handler de erro central que registra o log e responde 500 genérico (T-13).

### [MEDIUM] F-16 — Código duplicado
Pattern: AP-16
File: models.py:12-21, 31-40, 304-313, 79-86, 95-102, 171-201, 203-233
Description: O mapeamento linha→dicionário de produto aparece 3 vezes e o de usuário 2 vezes. get_pedidos_usuario e get_todos_pedidos são idênticas exceto pelo WHERE.
Impact: Uma mudança de campo exige editar 3 lugares, e esquecer um deles gera respostas divergentes.
Recommendation: Funções únicas de serialização por entidade e uma consulta de pedidos parametrizada pelo filtro (T-15).

### [MEDIUM] F-17 — Infraestrutura misturada
Pattern: AP-17
File: database.py:7-86
File: app.py:7-8
Description: get_db abre a conexão, executa o DDL das 4 tabelas e o seed (produtos e usuários) na mesma função, e a config fica atribuída no entry point.
Impact: Não dá para criar o schema sem conectar nem conectar sem semear, e o seed roda no caminho de qualquer requisição.
Recommendation: Separar connection, schema e seed, e mover a config para um módulo próprio (T-01, T-09).

### [MEDIUM] F-18 — Contrato de resposta inconsistente
Pattern: AP-19
File: controllers.py:20, 70, 142, 206, 292
File: models.py:275-283
Description: Alguns erros trazem "sucesso": False (20, 206) e outros não (70, 142). health usa {"status","detalhes"}. atualizar_status_pedido responde 200 "Status atualizado" mesmo quando o pedido não existe.
Impact: Clientes precisam tratar formatos diferentes, e a atualização de um pedido inexistente parece ter funcionado.
Recommendation: Unificar a montagem de resposta mantendo status e chaves atuais. Padronizar o formato fica como recomendação (T-13).

### [LOW] F-19 — Números e strings mágicos
Pattern: AP-20
File: models.py:257-262
File: controllers.py:47-50, 52, 242
File: app.py:36
Description: Faixas de desconto (10000/0.1, 5000/0.05, 1000/0.02), limites de nome (2/200), a lista de categorias e a lista de status estão inline. A versão "1.0.0" se repete em app.py:36 e controllers.py:285.
Impact: Mudar uma regra comercial exige achar literais espalhados pelo código.
Recommendation: Constantes nomeadas no model do domínio (T-17).

### [LOW] F-20 — Nomenclatura ruim
Pattern: AP-21
File: models.py:24, 54, 65, 89, 187, 191, 219, 223
File: controllers.py:14, 56, 64, 98, 136, 160
Description: O parâmetro e a variável `id` sombreiam o builtin, há cursores nomeados cursor2/cursor3 e os prefixos misturam inglês e português (get_todos_produtos).
Impact: Fica mais difícil de ler e de buscar no código.
Recommendation: Nomes descritivos (produto_id, usuario_id) e convenção única (T-17).

### [LOW] F-21 — Log por print
Pattern: AP-22
File: controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250
File: app.py:56, 83-86
Description: Log de aplicação feito com print, sem nível. Linhas 161, 179 e 182 registram o e-mail do usuário.
Impact: Não dá para filtrar nem desligar o log, e dados pessoais vão para o stdout.
Recommendation: Usar o módulo logging com níveis (T-17).

### [LOW] F-22 — Imports não usados
Pattern: AP-23
File: database.py:2
File: models.py:2
Description: `import os` em database.py e `import sqlite3` em models.py não são usados em nenhum outro ponto dos arquivos.
Impact: Ruído e falsa dependência entre módulos.
Recommendation: Remover (T-17).

## Deprecated APIs
None detected (checked against Flask 3.1.1, flask-cors 5.0.1 and the Python sqlite3 standard library).

## Proposed Target Structure
```
code-smells-project/
├── app.py                        # composition root (mantido: python app.py)
├── config.py                     # criado — config lida do ambiente
├── .env.example                  # criado
├── requirements.txt              # mantido
├── database/
│   ├── __init__.py
│   ├── connection.py             # conexão por requisição (flask.g)
│   ├── schema.py                 # DDL
│   └── seed.py                   # dados de exemplo com senha em hash
├── models/
│   ├── produto_model.py
│   ├── usuario_model.py
│   ├── pedido_model.py
│   └── relatorio_model.py
├── services/
│   └── pedido_service.py         # criação de pedido (produtos+pedidos+itens) e notificações
├── controllers/
│   ├── produto_controller.py
│   ├── usuario_controller.py
│   ├── pedido_controller.py
│   ├── relatorio_controller.py
│   ├── health_controller.py
│   └── admin_controller.py
├── views/
│   └── routes.py                 # mapeamento URL → controller (mesmas rotas)
├── middlewares/
│   ├── error_handler.py
│   └── admin_guard.py
└── validators/
    └── validators.py             # regras de entrada compartilhadas
```
models.py, controllers.py e database.py viram pacotes divididos por domínio. app.py deixa de ter handlers e só monta a aplicação. Rotas, métodos e formatos de resposta continuam iguais.

================================
Total: 22 findings
================================
