# Catálogo de Anti-Patterns

Guia da Fase 2. Cada entrada tem: o que é, **sinais de detecção** verificáveis no código, severidade padrão e a transformação do playbook que a resolve. Os sinais descrevem o comportamento; os trechos de busca são atalhos para as linguagens mais comuns — adapte ao stack detectado.

## Régua de severidade

| Severidade | Definição |
|---|---|
| **CRITICAL** | Falha grave de arquitetura ou segurança: impede o funcionamento correto, expõe dados sensíveis ou viola completamente a separação de responsabilidades |
| **HIGH** | Forte violação de MVC ou SOLID que dificulta muito manutenção e testes |
| **MEDIUM** | Problema de padronização, duplicação ou performance moderada |
| **LOW** | Legibilidade, nomenclatura, números mágicos |

Desempate: se o problema permite a um cliente HTTP anônimo **ler, alterar ou destruir dados** que não deveria, é CRITICAL. Se só atrapalha quem mantém o código, é no máximo HIGH. A severidade padrão pode subir um nível quando o impacto concreto no projeto justificar, e a justificativa vai no campo `Impact`.

## Índice

| ID | Anti-pattern | Severidade | Fix |
|---|---|---|---|
| AP-01 | Credenciais e segredos hardcoded | CRITICAL | T-01 |
| AP-02 | Injeção (SQL, comando, execução arbitrária) | CRITICAL | T-02 |
| AP-03 | Armazenamento inseguro de senha | CRITICAL | T-03 |
| AP-04 | Exposição de dados sensíveis | CRITICAL | T-04 |
| AP-05 | God Class / God Module / God Method | CRITICAL | T-05 |
| AP-06 | Controle de acesso ausente ou falso | CRITICAL | T-06 |
| AP-07 | Regra de negócio ou acesso a dados no controller/rota | HIGH | T-07 |
| AP-08 | Camada ausente, morta ou com responsabilidade trocada | HIGH | T-08 |
| AP-09 | Estado global mutável e acoplamento sem injeção de dependência | HIGH | T-09 |
| AP-10 | Configuração insegura de execução | HIGH | T-01 |
| AP-11 | Escrita em várias etapas sem transação | HIGH | T-10 |
| AP-12 | Queries N+1 | MEDIUM | T-11 |
| AP-13 | Validação de entrada ausente ou duplicada | MEDIUM | T-12 |
| AP-14 | Tratamento de erro ausente, genérico ou repetido | MEDIUM | T-13 |
| AP-15 | APIs deprecated | MEDIUM | T-14 |
| AP-16 | Código duplicado | MEDIUM | T-15 |
| AP-17 | Infraestrutura misturada (schema, seed, config no lugar errado) | MEDIUM | T-01, T-09 |
| AP-18 | Fluxo assíncrono aninhado (callback hell) | MEDIUM | T-16 |
| AP-19 | Contrato de resposta inconsistente | MEDIUM | T-13 |
| AP-20 | Números e strings mágicos | LOW | T-17 |
| AP-21 | Nomenclatura ruim | LOW | T-17 |
| AP-22 | Log por `print`/`console.log` | LOW | T-17 |
| AP-23 | Código morto, imports e dependências não usados | LOW | T-17 |

---

## CRITICAL

### AP-01 — Credenciais e segredos hardcoded

Segredo escrito como literal no código-fonte versionado.

**Sinais**
- Atribuição de literal a nome contendo `secret`, `password`, `passwd`, `pwd`, `senha`, `token`, `api_key`, `apikey`, `private_key`, `credential`
- Literal com prefixo de chave real: `sk_live_`, `pk_live_`, `AKIA`, `ghp_`, `xox`, `-----BEGIN`
- String de conexão com usuário e senha embutidos (`://user:pass@`)
- Objeto de configuração com usuário/senha de banco, SMTP ou gateway
- Busca: `(secret|passw|pwd|senha|token|api_?key)\w*\s*[:=]\s*['"]`

**Não é finding**: leitura de variável de ambiente; valor de exemplo em `.env.example`; senha de usuário em script de seed (isso é AP-03 se gravada sem hash).

### AP-02 — Injeção (SQL, comando, execução arbitrária)

Entrada externa compõe uma instrução executável.

**Sinais**
- Query montada por concatenação, interpolação ou formatação: `"... WHERE id = " + x`, `f"SELECT ... {x}"`, `"...%s" % x`, `` `SELECT ... ${x}` ``, `.format(`
- `execute(`/`query(`/`raw(` recebendo variável construída em vez de literal com placeholders
- Endpoint que recebe SQL, comando ou código no corpo da requisição e executa
- `eval(`, `exec(`, `os.system(`, `subprocess(..., shell=True)`, `child_process.exec(` com dado do usuário
- Busca: `execute\(|\.query\(|\.raw\(|\.run\(|\.all\(|\.get\(` e inspecione o argumento

**Não é finding**: query com placeholders (`?`, `%s` com tupla separada, `$1`, `:nome`); método de ORM que parametriza. `LIKE` com valor interpolado no ORM não é injeção de SQL.

Cada ponto de injeção é uma faixa de linha. Um mesmo arquivo com 20 queries concatenadas gera **um** finding com as 20 faixas.

### AP-03 — Armazenamento inseguro de senha

**Sinais**
- Senha gravada como recebida (INSERT/UPDATE com o campo de senha sem transformação)
- Hash rápido ou sem salt: `md5`, `sha1`, `sha256` direto sobre a senha
- "Criptografia" caseira: base64, XOR, substring, laço repetindo codificação
- Comparação de senha por igualdade simples (`==`, `===`, `WHERE senha = ...`)
- Senha padrão atribuída quando o usuário não informa uma
- Seed gravando senhas legíveis

**Não é finding**: `bcrypt`, `argon2`, `scrypt`, `PBKDF2` com salt, ou o helper de hash de senha do framework.

### AP-04 — Exposição de dados sensíveis

Dado que nunca deveria sair do servidor aparece em resposta HTTP ou em log.

**Sinais**
- Serializador/`to_dict`/`toJSON` que inclui campo de senha, hash, token ou segredo
- `SELECT *` de tabela de usuários devolvido diretamente
- Endpoint (health, debug, info) que devolve configuração, chave, caminho de banco ou flag de debug
- Log contendo senha, número de cartão, token ou chave
- Resposta de erro devolvendo `str(e)`, `err.message` ou stack trace ao cliente

Para cada serializador vulnerável, liste também as rotas que o utilizam.

### AP-05 — God Class / God Module / God Method

Uma unidade concentra responsabilidades que deveriam estar em camadas ou domínios diferentes.

**Sinais** (dois ou mais)
- Uma classe ou arquivo que faz ao mesmo tempo: conexão/schema de banco, registro de rotas e regra de negócio
- Um arquivo com acesso a dados de 3 ou mais entidades sem relação direta
- Nomes genéricos: `Manager`, `Handler`, `Utils`, `Helper`, `Main`, `App*` com centenas de linhas
- Método/handler com mais de ~50 linhas ou mais de 4 níveis de aninhamento
- Classe com um único método que registra todas as rotas com os handlers inline

Reporte a faixa completa da unidade (`arquivo:início-fim`) e enumere as responsabilidades encontradas.

### AP-06 — Controle de acesso ausente ou falso

**Sinais**
- Rota `destructive` (apaga em massa, reseta banco, executa comando) sem verificação de credencial
- Rota sob `/admin` ou que devolve dados financeiros/pessoais de todos os usuários, sem guarda
- Token previsível ou fixo (`"fake-token-" + id`, contador, id em base64)
- Cliente define o próprio privilégio: campo `role`/`tipo`/`is_admin` aceito do corpo da requisição no cadastro
- Nenhum middleware/decorator de autenticação no projeto inteiro

A correção na Fase 3 é proporcional: guarda nas rotas `destructive`/administrativas e remoção de privilégio autoatribuído. Introduzir autenticação em **todas** as rotas mudaria o contrato; isso é registrado como adiado.

---

## HIGH

### AP-07 — Regra de negócio ou acesso a dados no controller/rota

**Sinais**
- Handler de rota chamando o banco diretamente (`cursor.execute`, `db.session`, `Model.query`, `db.run`, `repository.` inline)
- Cálculo de domínio dentro do handler: totais, descontos, percentuais, transições de status, regras de elegibilidade
- Efeito colateral disparado do handler: envio de e-mail, notificação, escrita em log de auditoria
- Handler montando manualmente o dicionário de resposta campo a campo
- Handler com mais de ~25 linhas

**Regra de bolso**: um controller saudável lê a entrada, chama **uma** operação de model/service e traduz o resultado em resposta.

### AP-08 — Camada ausente, morta ou com responsabilidade trocada

Vale principalmente para projetos N1 e N2: as pastas sugerem arquitetura que o código não cumpre.

**Sinais**
- Não existe camada entre a rota e os dados (rotas fazem tudo; não há controllers)
- Módulo de service, helper ou validação que **nenhum outro arquivo importa** — busque o nome do módulo e de cada símbolo exportado
- Função utilitária que reimplementa o que as rotas duplicam inline (a abstração existe e é ignorada)
- Recurso dentro do módulo errado (ex.: CRUD de uma entidade no arquivo de rotas de outra)
- Model contendo objetos de requisição/resposta HTTP; rota contendo DDL
- Camada inferior importando camada superior (model importando controller)

### AP-09 — Estado global mutável e acoplamento sem injeção de dependência

**Sinais**
- Variável de módulo reatribuída em função (`global x`, `let cache = {}` alterado por funções exportadas)
- Conexão de banco única em variável global compartilhada entre requisições/threads
- Cache em memória sem limite nem expiração
- Contadores/acumuladores de negócio em variável de módulo
- Dependência instanciada dentro de quem a usa (`new Database()` no construtor, `import` de singleton concreto) sem possibilidade de substituição
- Valor primitivo exportado e alterado depois (o importador nunca vê a mudança)

### AP-10 — Configuração insegura de execução

**Sinais**
- Modo debug fixo no código: `debug=True`, `DEBUG = True`, `app.run(debug=True)`
- Bind em todas as interfaces combinado com debug
- CORS liberado para qualquer origem sem configuração (`CORS(app)` puro, `origin: '*'`)
- Porta, host, URI de banco fixos no entry point, sem leitura do ambiente

### AP-11 — Escrita em várias etapas sem transação

**Sinais**
- Dois ou mais INSERT/UPDATE/DELETE dependentes sem `BEGIN`/`commit`+`rollback`, bloco transacional ou unit of work
- `commit` no fim sem `rollback` no caminho de erro
- Retorno antecipado no meio de uma sequência de escritas
- Exclusão de registro pai sem tratar os filhos (órfãos) e sem `ON DELETE CASCADE`
- Leitura de saldo/estoque seguida de escrita sem atomicidade

---

## MEDIUM

### AP-12 — Queries N+1

**Sinais**
- Chamada ao banco dentro de `for`/`forEach`/`map`/`while` que percorre o resultado de outra query
- Acesso a relacionamento lazy dentro de laço (`len(u.tasks)`, `item.produto.nome`)
- Callbacks aninhados em que cada nível faz uma query por item do nível anterior
- Contagens por item (`count()` dentro de laço) em vez de `GROUP BY`
- Vários `COUNT` separados na mesma tabela variando só o filtro

### AP-13 — Validação de entrada ausente ou duplicada

**Sinais**
- Uso do corpo da requisição sem verificar se existe (`dados.get` com `dados` possivelmente nulo)
- Comparação numérica sobre valor sem checagem de tipo (`if preco < 0` com `preco` vindo do JSON)
- Conversão sem tratamento (`int(x)`, `parseInt`) de parâmetro de query
- Só presença é verificada; formato (e-mail, data, faixa, enumeração) não
- O mesmo bloco de validação copiado entre criar e atualizar
- Regras divergentes para o mesmo campo em lugares diferentes

### AP-14 — Tratamento de erro ausente, genérico ou repetido

**Sinais**
- `except:` sem tipo, `catch (e) {}` vazio, `except Exception: pass`
- Parâmetro de erro do callback ignorado (`(err, row) => { use(row) }` sem testar `err`)
- O mesmo `try/except` devolvendo 500 copiado em todos os handlers
- Nenhum handler de erro central (`errorhandler`, middleware de 4 argumentos, `@ControllerAdvice`)
- Resposta de sucesso enviada mesmo quando a operação falhou

### AP-15 — APIs deprecated

Verificação obrigatória em toda auditoria. Compare as chamadas do código com as versões do manifesto e do runtime. Reporte a API usada, desde quando é obsoleta e o equivalente moderno.

| Stack | Obsoleto | Usar |
|---|---|---|
| Python ≥ 3.12 | `datetime.utcnow()`, `datetime.utcfromtimestamp()` | `datetime.now(timezone.utc)`, `datetime.fromtimestamp(ts, timezone.utc)` |
| Python | `imp`, `distutils`, `pkg_resources`, `asyncio.get_event_loop()` fora de loop, `logger.warn()`, `assertEquals` | `importlib`, `setuptools`/`sysconfig`, `importlib.metadata`, `asyncio.run()`, `logger.warning()`, `assertEqual` |
| SQLAlchemy ≥ 1.4 / 2.x | `Query.get()` / `Model.query.get(id)`, `session.query(M).get(id)` | `session.get(Model, id)` |
| SQLAlchemy 2.x | `declarative_base()` de `ext.declarative`, `engine.execute()` | `sqlalchemy.orm.DeclarativeBase`, `connection.execute()` |
| Flask ≥ 2.3 | `@app.before_first_request`, `flask.json.JSONEncoder`, `app.env`/`FLASK_ENV`, `_app_ctx_stack` | inicialização explícita na factory, `app.json` provider, `FLASK_DEBUG`, `g`/`current_app` |
| Node.js | `new Buffer()`, `url.parse()`, `querystring`, `fs.exists()`, `crypto.createCipher()`, `util.isArray()`, `String.prototype.substr`, módulo `domain` | `Buffer.from()`, `new URL()`, `URLSearchParams`, `fs.access`/`existsSync`, `createCipheriv()`, `Array.isArray()`, `slice`/`substring`, `AsyncLocalStorage` |
| Express ≥ 4.16 | pacote `body-parser` separado, `req.param()`, `res.send(status)`, `res.json(status, obj)`, `app.del()` | `express.json()`, `req.params/query/body`, `res.sendStatus()`, `res.status().json()`, `app.delete()` |
| npm | `request`, `node-uuid`, `moment` em código novo | `fetch`/`undici`, `crypto.randomUUID()`, `Intl`/`date-fns` |
| Java | `new Date(y, m, d)`, `Thread.stop()`, `new Integer(x)`, `javax.*` em Jakarta EE 9+ | `java.time`, interrupção cooperativa, `Integer.valueOf`, `jakarta.*` |
| PHP | `mysql_*`, `each()`, `create_function()` | PDO/`mysqli`, `foreach`, closures |

Se o stack não está na tabela, verifique as notas de versão do framework na versão do manifesto. Sem certeza de que a API é obsoleta naquela versão, não reporte.

Dependência com versão fixada muito antiga ou pacote descontinuado também entra aqui.

**Não é finding**: algoritmo fraco (isso é AP-03), estilo antigo que continua suportado.

### AP-16 — Código duplicado

**Sinais**
- O mesmo mapeamento linha → dicionário repetido em várias funções
- A mesma regra de negócio reescrita em vários handlers (principalmente quando já existe um método que a implementa)
- Funções quase idênticas que diferem por um filtro
- A mesma expressão regular ou lista de valores válidos em mais de um arquivo

Reporte todas as cópias e, se existir, a implementação canônica que deveria ter sido usada.

### AP-17 — Infraestrutura misturada

**Sinais**
- DDL (`CREATE TABLE`) e dados de seed dentro da função que abre a conexão
- Seed executado em toda inicialização da aplicação
- Configuração (URI, chave, flags) atribuída no entry point em vez de módulo de config
- Biblioteca de leitura de `.env` declarada no manifesto e nunca usada
- Banco apenas em memória em código que se apresenta como produção

### AP-18 — Fluxo assíncrono aninhado (callback hell)

**Sinais**
- Callbacks aninhados em 4 ou mais níveis
- Contadores manuais para saber quando operações paralelas terminaram (`pending--; if (pending === 0)`)
- `const self = this` para atravessar callbacks
- A mesma resposta HTTP podendo ser enviada por mais de um caminho

### AP-19 — Contrato de resposta inconsistente

**Sinais**
- Algumas rotas respondem JSON e outras texto puro
- Formatos de erro diferentes (`{"erro":...}`, `{"error":...}`, string)
- Status incoerente com o resultado (200 em falha, 404 para erro de banco)

A correção unifica o tratamento **sem alterar** status e chaves que os clientes já consomem; padronizar o formato em si é mudança de contrato e fica como recomendação.

---

## LOW

### AP-20 — Números e strings mágicos

**Sinais**: limites, percentuais, tamanhos, timeouts e códigos como literais no meio da lógica; listas de status/papéis repetidas inline; constantes que já existem em algum módulo mas são ignoradas.

### AP-21 — Nomenclatura ruim

**Sinais**: variáveis de uma ou duas letras fora de índice de laço (`u`, `e`, `p`, `cc`, `t`), abreviações opacas em nomes públicos, nome que sombreia builtin (`id`, `type`, `list`), nomes que mentem sobre o conteúdo, mistura de convenções no mesmo arquivo.

### AP-22 — Log por `print`/`console.log`

**Sinais**: `print(`, `console.log(`, `System.out.println(` usados como log de aplicação; sem nível nem formato; mensagens com dados pessoais.

### AP-23 — Código morto, imports e dependências não usados

**Sinais**: import cujo nome não aparece no resto do arquivo; símbolo exportado sem importador; função sem chamador; dependência do manifesto sem import correspondente; parâmetro nunca lido.

---

## Procedimento de varredura

1. Para cada AP, rode as buscas indicadas em todo o código-fonte e abra cada resultado para confirmar no contexto. Busca encontra candidatos; quem decide é a leitura.
2. Anote `arquivo:linha-início[-linha-fim]` de cada ocorrência confirmada.
3. Para AP-08 e AP-23, a evidência é a **ausência** de uso: busque o símbolo no projeto inteiro antes de afirmar que ninguém o usa.
4. Um trecho pode violar mais de um padrão (ex.: handler com SQL concatenado é AP-02 e AP-07). Reporte em ambos, cada um com seu impacto.
5. Não infle o relatório: ocorrências do mesmo padrão no mesmo arquivo formam um finding só.
