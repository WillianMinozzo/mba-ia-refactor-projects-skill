# Guidelines de Arquitetura — MVC alvo

Guia da Fase 3. Define para onde o projeto vai: quais camadas existem, o que cada uma pode e não pode fazer, e como adaptar a intervenção ao estado atual do projeto.

## 1. Camadas e responsabilidades

```
Requisição HTTP
      │
      ▼
┌──────────────┐   mapeia URL+método → controller; serializa a resposta
│ View/Routes  │
└──────┬───────┘
       ▼
┌──────────────┐   lê e valida a entrada, chama model/service, escolhe o status
│ Controller   │
└──────┬───────┘
       ▼
┌──────────────┐   regra envolvendo vários models ou efeito externo (opcional)
│ Service      │
└──────┬───────┘
       ▼
┌──────────────┐   dados + regras do domínio; único lugar que fala com o banco
│ Model        │
└──────────────┘

Transversais: Config (ambiente) · Middlewares (erro, guarda) · Entry point (composition root)
```

| Camada | Faz | Não faz |
|---|---|---|
| **Model** | Acesso a dados (queries, ORM), invariantes e regras do domínio (cálculos, transições de estado, `is_overdue`), transações, representação serializável (`to_dict`) sem campos sensíveis | Conhecer requisição/resposta HTTP, status code, framework web |
| **View / Routes** | Declarar rota → controller, aplicar guardas, formatar a resposta (JSON, template) | Regra de negócio, acesso a dados, validação de domínio |
| **Controller** | Extrair parâmetros, validar formato da entrada, chamar **uma** operação de model/service, traduzir resultado ou erro de domínio em resposta | SQL/ORM direto, cálculo de negócio, envio de notificação inline, `try/except` genérico |
| **Service** (opcional) | Orquestrar regra que envolve vários models; integrar sistemas externos (e-mail, pagamento) | Conhecer HTTP; duplicar o que é de um model só |
| **Config** | Ler o ambiente, expor valores tipados, definir padrões seguros | Conter segredo literal; ser alterada em tempo de execução |
| **Middleware** | Tratamento de erro central, guarda de acesso, log de requisição | Regra de negócio |
| **Entry point** | Montar tudo: config → dados → rotas → middlewares → subir servidor | Declarar rotas inline, conter regra, conter config literal |

Em uma API JSON, a "View" é a combinação de rotas (mapeamento HTTP) e serialização da resposta. Não crie templates onde não existem.

## 2. Direção de dependência

```
routes → controllers → (services) → models → infraestrutura de dados
            ↑                                        ↑
        middlewares                                config
```

- Uma camada só importa a camada imediatamente abaixo (ou a seguinte, quando não há service).
- Nunca para cima: model não importa controller; controller não importa routes.
- Config é importada por quem precisa; não importa ninguém.
- Dependências entram por parâmetro (construtor, factory, argumento), não por variável global.

## 3. Regras por camada

**Model**
- Um arquivo por entidade ou agregado. Nada de `models.py` com todos os domínios.
- Toda query parametrizada. Nenhuma string de SQL montada com dado externo.
- Operação com mais de uma escrita é uma transação: tudo ou nada.
- Erros de domínio são exceções/resultados nomeados (`NotFound`, `ValidationError`, `BusinessRuleError`), não dicionários `{"erro": ...}`.
- Um único mapeamento linha → objeto por entidade.

**Controller**
- Um arquivo por recurso. Funções curtas (referência: até ~20 linhas).
- Não captura exceção genérica: deixa subir para o handler central.
- Não conhece SQL nem o objeto de conexão.

**Routes**
- Um módulo por recurso, agrupado no mecanismo do framework (Blueprint, Router, grupo de rotas).
- Caminhos e métodos idênticos aos originais.

**Middlewares**
- Um handler central converte exceções em respostas: erro de domínio → 4xx correspondente; erro inesperado → 500 com mensagem genérica e detalhe apenas em log.
- Formato do corpo de erro igual ao que a aplicação já devolvia (mesma chave), para não quebrar clientes.

**Config**
- Tudo que varia por ambiente vem de variável de ambiente: segredos, URI de banco, debug, host, porta, origens de CORS.
- Valores não sensíveis têm padrão igual ao comportamento original (mesma porta, mesmo arquivo de banco).
- Segredo sem variável definida: fora de produção, gerar valor aleatório efêmero e avisar em log; em produção, falhar no boot. A aplicação precisa subir em desenvolvimento sem `.env`.
- Debug desligado por padrão.
- Criar `.env.example` com todas as variáveis e garantir `.env` no `.gitignore`.

**Entry point**
- Mantém o caminho e o comando de boot originais sempre que possível.
- Preferir uma função factory (`create_app()`), que monta e devolve a aplicação, com o bloco de execução chamando-a. Isso permite testar sem subir servidor.
- Criação de schema e seed ficam em módulo/script próprio, chamados explicitamente — não como efeito colateral de abrir conexão.

## 4. Estrutura alvo

Crie as camadas dentro da **raiz de código existente** (o diretório do entry point; `src/` se o projeto já usa). Não introduza um `src/` que não existia nem mova o entry point sem necessidade.

Genérica:

```
<raiz de código>/
├── config/            # leitura do ambiente
├── database/          # conexão/sessão, schema, seed
├── models/            # um arquivo por entidade
├── services/          # opcional
├── controllers/       # um arquivo por recurso
├── routes/            # (ou views/) um arquivo por recurso
├── middlewares/       # error handler, guardas
└── <entry point>      # composition root
```

Exemplo Python/Flask:

```
app.py                      # create_app() + execução
config/settings.py
database/connection.py      # get_db por requisição ou sessão do ORM
database/schema.py · seed.py
models/produto_model.py · usuario_model.py · pedido_model.py
controllers/produto_controller.py · ...
routes/produto_routes.py · ...  (Blueprints)
middlewares/error_handler.py · auth.py
```

Exemplo Node/Express:

```
src/app.js                  # composition root + listen
src/config/index.js
src/database/connection.js · schema.js · seed.js
src/models/userModel.js · courseModel.js · ...
src/services/checkoutService.js
src/controllers/checkoutController.js · ...
src/routes/checkoutRoutes.js · index.js  (express.Router)
src/middlewares/errorHandler.js · auth.js
```

Convenções:
- Use o padrão de nomes já presente no projeto (idioma do domínio, `snake_case`/`camelCase`, sufixos). Não traduza nomes de entidades, rotas nem campos.
- Se já existe pasta para a camada (`routes/`, `models/`), reutilize o nome. Se não existe, use `routes/` para APIs.
- Arquivos de pacote exigidos pela linguagem (`__init__.py`, `index.js`) acompanham cada pasta.

## 5. Adaptação ao nível de organização

A intervenção é proporcional ao que o projeto já tem. Refatorar não é reescrever.

| Nível | O que fazer | O que evitar |
|---|---|---|
| **N0 — Monolito sem camadas** | Criar todas as camadas. Decompor a classe/arquivo único por recurso: SQL → models, fluxo → controllers (ou services se envolver vários models), registro → routes. Remover a unidade original ao final. | Mover o monolito inteiro para uma pasta e chamar de camada |
| **N1 — Camadas por arquivo** | Transformar cada arquivo-camada em pasta e dividir por domínio. Devolver a cada camada o que vazou para a outra. | Manter um arquivo único por camada |
| **N2 — Parcialmente em camadas** | **Manter** o que já está correto. Criar só a camada que falta (em geral controllers e config). Mover o que está no módulo errado. Passar a **usar** services/helpers existentes ou removê-los se redundantes. | Renomear pastas que já funcionam, recriar models que estão corretos, mudar de ORM, trocar o estilo do projeto |

Em N2, antes de criar qualquer arquivo, liste o que já existe para a mesma finalidade. Se há um método canônico (ex.: `is_overdue()` no model) e cópias inline, a correção é usar o canônico e apagar as cópias.

## 6. Preservação de contrato

- Mesmos caminhos, métodos, parâmetros, status e chaves de resposta.
- Mesma porta, mesmo comando de boot e mesmo arquivo de banco padrão.
- Mudanças permitidas, sempre declaradas como intencionais no resumo final:
  - remover campo sensível de respostas (senha, hash, segredo, config interna);
  - exigir credencial em rotas `destructive`/administrativas (401/403 sem ela; comportamento original com ela);
  - ignorar privilégio autoatribuído vindo do cliente;
  - trocar o detalhe técnico de um erro 500 por mensagem genérica.
- Não incluído no escopo (registrar como adiado): introduzir autenticação em todas as rotas, paginação obrigatória, renomear campos ou rotas, trocar banco ou framework.

## 7. Checklist de saída

- [ ] Estrutura de diretórios segue o padrão MVC
- [ ] Configuração em módulo próprio, nenhum segredo literal no código
- [ ] Models abstraem todo o acesso a dados
- [ ] Views/Routes separadas, sem lógica
- [ ] Controllers concentram o fluxo, sem acesso direto ao banco
- [ ] Tratamento de erro centralizado
- [ ] Entry point claro (composition root)
- [ ] Nenhum import de camada superior por camada inferior
- [ ] Nenhum arquivo antigo remanescente duplicando código novo
- [ ] Comando de boot original funciona
