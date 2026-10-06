# Análise de Projeto — Heurísticas

Guia da Fase 1. Tudo aqui é detecção por evidência: um arquivo que existe, uma linha que declara, uma chamada que aparece. Quando dois sinais conflitam, vale o manifesto de dependências.

## 1. Linguagem e gerenciador de pacotes

O manifesto na raiz decide. A extensão predominante dos arquivos-fonte confirma.

| Manifesto encontrado | Linguagem | Instalação | Observação |
|---|---|---|---|
| `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py` | Python | `pip install -r requirements.txt` / `poetry install` / `pipenv install` | Use `python`; se não existir, `python3` |
| `package.json` | JavaScript/TypeScript | `npm install` (ou `pnpm`/`yarn` se houver o lockfile correspondente) | `tsconfig.json` ou `.ts` ⇒ TypeScript |
| `pom.xml`, `build.gradle(.kts)` | Java/Kotlin | `mvn -q package` / `gradle build` | |
| `go.mod` | Go | `go mod download` | |
| `composer.json` | PHP | `composer install` | |
| `Gemfile` | Ruby | `bundle install` | |
| `*.csproj`, `*.sln` | C# | `dotnet restore` | |
| `Cargo.toml` | Rust | `cargo build` | |

Sem manifesto: decida pela extensão dos arquivos e registre "manifesto ausente" como finding de configuração.

## 2. Framework

Procure a dependência no manifesto **e** a instanciação no código. A versão reportada é a do manifesto.

| Stack | Dependência | Assinatura no código |
|---|---|---|
| Flask | `flask` | `Flask(__name__)`, `@app.route`, `Blueprint(` |
| FastAPI | `fastapi` | `FastAPI()`, `APIRouter(`, `@app.get` |
| Django | `django` | `manage.py`, `urlpatterns`, `settings.py` |
| Express | `express` | `express()`, `app.get(`, `express.Router()` |
| Fastify / Koa / Hapi | `fastify` / `koa` / `@hapi/hapi` | `fastify()`, `new Koa()`, `Hapi.server(` |
| NestJS | `@nestjs/core` | `@Controller(`, `@Module(` |
| Spring | `spring-boot-starter-web` | `@RestController`, `@SpringBootApplication` |
| Gin / Echo / net/http | `gin-gonic/gin` / `labstack/echo` | `gin.Default()`, `http.HandleFunc(` |
| Laravel / Slim | `laravel/framework` / `slim/slim` | `Route::get(`, `artisan` |
| Rails / Sinatra | `rails` / `sinatra` | `config/routes.rb`, `get '/' do` |
| ASP.NET | `Microsoft.AspNetCore.*` | `[ApiController]`, `app.MapGet(` |

Sem framework web: descreva como "aplicação sem framework HTTP" e aplique MVC às camadas equivalentes (entrada, orquestração, dados).

## 3. Banco de dados e forma de acesso

| Sinal | Conclusão |
|---|---|
| `sqlite3.connect(`, `new sqlite3.Database(`, arquivo `*.db`/`*.sqlite`, `:memory:` | SQLite, driver puro |
| `psycopg`, `pg`, `postgres://` | PostgreSQL |
| `mysql`, `pymysql`, `mysql2` | MySQL/MariaDB |
| `pymongo`, `mongoose`, `mongodb://` | MongoDB |
| `SQLAlchemy`, `flask_sqlalchemy`, `db.Model` | ORM SQLAlchemy |
| `sequelize`, `typeorm`, `prisma`, `knex` | ORM / query builder Node |
| `Hibernate`, `@Entity`, `JpaRepository` | JPA |
| `gorm`, `Eloquent`, `ActiveRecord` | ORM do respectivo stack |

Registre também: onde a conexão é criada, se é global/singleton, onde o schema é definido (DDL em código, migrations, `create_all`) e onde ficam os dados de seed.

**Tabelas/entidades**: extraia de `CREATE TABLE`, de classes de model (`__tablename__`, `@Entity`, `sequelize.define`) ou de migrations. Liste pelo nome real.

## 4. Domínio de negócio

Infira a partir de três fontes, nesta ordem: nomes de tabelas/entidades, caminhos das rotas e README/descrição do manifesto. Descreva em uma frase com as entidades principais, no formato `<tipo de sistema> (<entidade>, <entidade>, ...)`.

Não copie o nome da pasta nem do pacote: eles frequentemente não correspondem ao que o código faz. Se o nome do projeto diz uma coisa e as entidades dizem outra, vale o que o código faz.

## 5. Contagem de arquivos e linhas

- **Source files**: arquivos de código da aplicação (`.py`, `.js`, `.ts`, `.java`, `.go`, `.php`, `.rb`, `.cs`...). Inclui scripts de seed e utilitários. Exclui tudo que está fora do escopo de leitura, além de manifestos, lockfiles, Markdown e arquivos de exemplo de requisição.
- **Lines of code**: soma das linhas desses arquivos, obtida por contagem real (`wc -l` ou equivalente), reportada com `~`.

O número reportado tem de bater com o que foi lido. Se listou 15 arquivos, leu 15.

## 6. Inventário de rotas

Uma linha por rota: método, caminho, handler, `arquivo:linha` do registro.

| Framework | Onde as rotas são registradas |
|---|---|
| Flask | `@app.route`, `@bp.route`, `app.add_url_rule(`; prefixos em `register_blueprint(..., url_prefix=)` |
| FastAPI | `@app.get/post/...`, `include_router(prefix=)` |
| Django | `urlpatterns` em `urls.py`, `include(` |
| Express/Koa/Fastify | `app.METHOD(`, `router.METHOD(`, `app.use('/prefixo', router)` |
| Spring | `@GetMapping`, `@RequestMapping` em classe e método |
| Outros | tabela de rotas do framework |

Componha o caminho completo com os prefixos. Marque cada rota com uma classe de risco, usada na validação:

| Classe | Critério | Como validar na Fase 3 |
|---|---|---|
| `read` | GET sem efeito colateral | Chamar e comparar status |
| `write` | Cria/altera um recurso | Chamar com payload válido; alterar/remover apenas o recurso criado no próprio teste |
| `destructive` | Apaga em massa, reseta banco, executa comando/SQL arbitrário | **Não chamar com efeito real.** Confirmar que a rota está registrada e que a guarda responde 401/403 sem credencial |

Fontes de payload válido, em ordem: arquivos de exemplo de requisição (`*.http`, coleções Postman, `curl` no README), regras de validação do próprio handler, dados de seed.

## 7. Nível de organização da arquitetura

Classifique em um dos três níveis. O nível determina o tamanho da intervenção na Fase 3.

| Nível | Sinais | Descrição típica |
|---|---|---|
| **N0 — Monolito sem camadas** | Rotas, regra de negócio e acesso a dados no mesmo arquivo ou na mesma classe; 1 a 3 arquivos concentram tudo | "Monolítica — tudo em N arquivos, sem separação de camadas" |
| **N1 — Camadas por arquivo** | Arquivos separados por papel técnico (`models.py`, `controllers.py`), mas cada arquivo mistura todos os domínios e as responsabilidades vazam entre eles | "Camadas por arquivo único — sem separação por domínio" |
| **N2 — Parcialmente em camadas** | Pastas por camada (`models/`, `routes/`, `services/`), mas com camada faltando, camada morta ou lógica na camada errada | "Parcialmente em camadas — <o que falta ou está fora do lugar>" |

Para decidir, responda com evidência:

1. Onde o SQL/ORM é chamado? (só em models, ou também em rotas/controllers?)
2. Onde ficam as regras de negócio? (cálculos, transições de estado, validações de domínio)
3. Existe uma camada entre a rota e os dados? Ela é chamada de fato?
4. Há pastas ou módulos que ninguém importa? (camada morta)
5. Algum módulo contém um recurso que não corresponde ao seu nome?

## 8. Ponto de entrada e comando de boot

| Stack | Onde procurar |
|---|---|
| Python | `if __name__ == "__main__"`, `app.run(`, `uvicorn.run(`, `manage.py`, `Procfile`, README |
| Node | `scripts.start` e `main` do `package.json`, `app.listen(` |
| Java | classe com `main` / `@SpringBootApplication`, `mvn spring-boot:run` |
| Go | `package main` + `func main()` |
| Outros | script de start do manifesto, `Procfile`, `Dockerfile` (`CMD`/`ENTRYPOINT`), README |

Registre o comando exato e a porta. Esse comando precisa continuar funcionando depois da refatoração.

## 9. Estratégia de validação (usada na Fase 3)

Escolha a primeira opção disponível para o stack:

1. **Cliente de teste em processo**, quando o framework oferece um sem dependência extra (ex.: `app.test_client()` no Flask, `TestClient` no FastAPI/Starlette se `httpx` estiver instalado, `Client` de teste do Django). Não abre porta, não deixa processo órfão.
2. **Servidor real em porta local**: suba com o comando de boot em segundo plano, aguarde a porta responder (tentativas curtas, limite de ~15 s), faça as requisições com o cliente HTTP da própria linguagem (`fetch` no Node 18+, `urllib` no Python) ou `curl`, e **encerre o processo** ao final.

Em qualquer dos casos:

- O teste de **boot** usa sempre o comando real de boot (opção 2), mesmo que os endpoints sejam exercitados pela opção 1.
- Escreva o script de verificação em um diretório temporário fora do projeto, nunca dentro dele.
- Os comandos precisam funcionar no sistema operacional e no shell em uso. Verifique quais executáveis existem antes de usá-los (`python` vs `python3`, `curl`) e prefira scripts na linguagem do próprio projeto a encadeamentos de shell.
- Para cada rota registre: método, caminho, status da linha de base e status depois. O critério de aprovação é mesmo status e mesmo formato de corpo (mesmas chaves de primeiro nível), salvo mudança intencional de contrato.
