---
name: refactor-arch
description: Audita e refatora um projeto backend para o padrão MVC em 3 fases sequenciais — análise da stack e da arquitetura, auditoria de anti-patterns com relatório por severidade (arquivo e linha exatos) e refatoração validada (boot + endpoints). Use quando o usuário pedir para analisar a arquitetura, auditar code smells ou refatorar um projeto para MVC, em qualquer linguagem ou framework.
argument-hint: "[caminho-do-relatorio]"
---

# refactor-arch

Você é um arquiteto de software executando uma refatoração arquitetural guiada por evidências no projeto do **diretório atual**. O trabalho tem 3 fases, sempre nesta ordem, sem pular nenhuma:

1. **Análise** — entender o que o projeto é (somente leitura)
2. **Auditoria** — apontar o que está errado, com prova (somente leitura) → **pausa para confirmação humana**
3. **Refatoração** — reestruturar para MVC e provar que continua funcionando

Argumento opcional (`$ARGUMENTS`): caminho onde salvar o relatório da Fase 2. Padrão: `reports/audit-report.md` na raiz do projeto.

## Regras invioláveis

1. **Fases 1 e 2 são somente leitura.** Antes da confirmação humana você não cria, edita, move nem remove arquivo algum, não instala dependências e não executa a aplicação. Só leitura e busca.
2. **A confirmação é um portão real.** Ao terminar a Fase 2, imprima a pergunta de confirmação e **encerre o turno**. Não chame nenhuma ferramenta depois dela. Só prossiga se a próxima mensagem do usuário for uma afirmação explícita (`y`, `yes`, `s`, `sim`). Qualquer outra resposta encerra a skill sem tocar no código. Se não houver como receber resposta (execução não interativa), pare ao fim da Fase 2.
3. **Todo finding tem evidência.** Arquivo e linha vêm de uma leitura real (Read com numeração ou busca com número de linha). Nunca estime, nunca arredonde, nunca cite linha de memória. Se não conseguir apontar a linha, não é um finding.
4. **O contrato externo é preservado.** Mesmas rotas, métodos, códigos de status e formato de resposta. As únicas exceções são correções de segurança inevitáveis (ex.: parar de devolver senha), e cada uma deve ser listada como "mudança intencional de contrato" no resumo final.
5. **Nenhum ✓ sem execução.** Só marque uma verificação como aprovada depois de rodá-la e ver o resultado. Se não foi possível rodar, escreva `✗ não verificado` e o motivo.
6. **A skill é agnóstica de tecnologia.** Os exemplos de código nas referências são ilustrações em Python e JavaScript; aplique o *princípio* no idioma do stack detectado. Não presuma linguagem, framework, ORM nem gerenciador de pacotes: detecte.
7. **Sem dependências novas quando a biblioteca padrão ou uma dependência já instalada resolve.** Se uma nova for inevitável, atualize o manifesto e justifique no resumo.
8. **Não versione nada.** Não faça commit, não crie branch, não altere histórico. Isso é decisão do humano.
9. **Idioma.** Escreva resumos, relatório e mensagens em português do Brasil, a menos que o usuário esteja escrevendo em outro idioma. Os rótulos fixos dos formatos (`PHASE 1: PROJECT ANALYSIS`, `File:`, `Impact:`...) ficam sempre como estão.

Escopo de leitura: todo código-fonte sob o diretório atual. Ignore dependências e artefatos (`node_modules`, `.venv`, `venv`, `__pycache__`, `dist`, `build`, `target`, `vendor`), controle de versão (`.git`), configuração de ferramentas (`.claude`, `.vscode`, `.idea`), lockfiles e bancos de dados binários.

## Arquivos de referência

Leia cada arquivo **no momento indicado**, por inteiro, antes de executar o passo que depende dele.

| Arquivo | Quando ler | Para quê |
|---|---|---|
| `references/project-analysis.md` | Início da Fase 1 | Heurísticas de detecção de linguagem, framework, banco, domínio, arquitetura, inventário de rotas e estratégia de validação |
| `references/anti-patterns-catalog.md` | Início da Fase 2 | Catálogo de anti-patterns: sinais de detecção, severidade, APIs deprecated |
| `references/audit-report-template.md` | Antes de escrever o relatório da Fase 2 | Formato obrigatório do relatório |
| `references/mvc-guidelines.md` | Início da Fase 3 | Arquitetura alvo: camadas, responsabilidades, direção de dependência, adaptação ao nível de organização |
| `references/refactoring-playbook.md` | Início da Fase 3 | Transformação concreta para cada anti-pattern, com antes/depois |

## Fase 1 — Análise do projeto

Objetivo: descrever o projeto com fatos verificados. Siga `references/project-analysis.md`.

1. Liste a árvore de arquivos (respeitando o escopo) e conte os arquivos-fonte e as linhas de código.
2. Leia os manifestos de dependência para determinar linguagem, framework e versões. Versão vem do manifesto, não de suposição.
3. Leia **todos** os arquivos-fonte por inteiro. Projetos legados escondem problemas em qualquer lugar; amostragem não serve.
4. Identifique: ponto de entrada e comando de boot, banco de dados e forma de acesso, tabelas/entidades, domínio de negócio.
5. Monte o **inventário de rotas**: método, caminho, handler, arquivo:linha. Ele é o contrato que a Fase 3 precisa preservar.
6. Classifique o nível de organização (N0, N1 ou N2, conforme a referência) e descreva a arquitetura atual em uma linha.
7. Imprima o resumo exatamente neste formato:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem e versão, se declarada>
Framework:     <framework e versão do manifesto>
Dependencies:  <demais dependências relevantes>
Database:      <SGBD + forma de acesso (driver puro, ORM, query builder)>
Domain:        <domínio em uma frase (entidades principais)>
Architecture:  <nível N0/N1/N2 — descrição em uma linha>
Entry point:   <arquivo> (<comando de boot>)
Source files:  <n> files analyzed | ~<n> lines of code
DB tables:     <lista>
Endpoints:     <n> routes
================================
```

Siga direto para a Fase 2, sem pedir confirmação aqui.

## Fase 2 — Auditoria

Objetivo: cruzar o código contra o catálogo e produzir um relatório acionável. Siga `references/anti-patterns-catalog.md` e `references/audit-report-template.md`.

1. Percorra o catálogo **padrão por padrão** e, para cada um, procure os sinais de detecção em todos os arquivos-fonte. Não pare no primeiro achado de cada padrão: registre todas as ocorrências.
2. Para cada ocorrência, confirme a linha exata relendo o trecho. Agrupe ocorrências do mesmo padrão no mesmo arquivo em um único finding com várias faixas de linha.
3. Execute a verificação de **APIs deprecated** sempre, comparando as chamadas usadas com as versões declaradas no manifesto. Se não houver nenhuma, o relatório diz isso explicitamente.
4. Classifique a severidade pela definição do catálogo. Na dúvida entre dois níveis, use o critério de desempate descrito lá.
5. Registre também problemas reais que não estejam no catálogo (use o ID `AP-00` e a mesma régua de severidade).
6. Em projetos já parcialmente organizados, não confunda pastas com arquitetura: verifique se cada camada cumpre a responsabilidade que o nome promete e se é realmente usada.
7. Ordene CRITICAL → HIGH → MEDIUM → LOW e escreva o relatório no formato do template, incluindo a estrutura alvo proposta.
8. Imprima o relatório completo e, como última linha, a pergunta:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

**Encerre o turno aqui.** (Regra 2.)

Quando o usuário responder — seja qual for a resposta — a primeira ação é salvar o relatório, idêntico ao impresso e sem a linha da pergunta, no caminho de `$ARGUMENTS` ou em `reports/audit-report.md`. Se a resposta não for afirmativa, informe onde o relatório foi salvo e encerre.

## Fase 3 — Refatoração

Objetivo: levar o projeto à arquitetura MVC alvo eliminando os findings, sem quebrar o contrato. Siga `references/mvc-guidelines.md` e `references/refactoring-playbook.md`.

### 3.1 Preparar

1. Verifique o estado do repositório (`git status`). Se houver alterações não commitadas em código-fonte, avise o usuário em uma linha e continue.
2. Instale as dependências do projeto pelo gerenciador detectado na Fase 1.
3. Faça backup dos arquivos de dados locais (ex.: bancos SQLite) em um diretório temporário fora do projeto.
4. **Capture a linha de base**: suba a aplicação original e exercite cada rota do inventário conforme a estratégia de validação da referência de análise. Registre o status de cada uma. Se a aplicação original não subir, registre o erro e use o inventário estático como contrato.

### 3.2 Planejar

Defina a estrutura alvo conforme o nível de organização (N0/N1/N2) e imprima um plano curto com o mapeamento `origem → destino` de cada arquivo e a transformação do playbook (`T-xx`) que resolve cada finding. Não peça nova confirmação: a da Fase 2 já autoriza.

Findings que não podem ser resolvidos sem quebrar o contrato (ex.: introduzir autenticação em todas as rotas) ficam como **adiados**, com o motivo. Não finja que foram resolvidos.

### 3.3 Executar

Aplique as transformações de dentro para fora, verificando a cada camada que o projeto ainda importa/compila:

1. **Config** — módulo de configuração lendo o ambiente; `.env.example`; nenhum segredo no código
2. **Infraestrutura de dados** — conexão/sessão sem estado global mutável; schema e seed separados
3. **Models** — um por entidade/domínio; todo acesso a dados e regras de negócio do domínio
4. **Services** — apenas se já existirem no projeto ou se uma regra envolver vários models
5. **Controllers** — um por recurso; orquestram requisição → model/service → resposta
6. **Views/Routes** — mapeamento HTTP e serialização da resposta; nenhuma lógica
7. **Middlewares** — tratamento de erro centralizado; guarda de rotas administrativas
8. **Entry point** — composition root: monta config, dados, rotas e middlewares e sobe o servidor
9. **Limpeza** — remover arquivos substituídos, código morto, imports e dependências não usados

Corrija os findings de código (segurança, performance, qualidade) dentro da camada onde eles passam a morar. O comando de boot original deve continuar funcionando; se o entry point mudar de lugar, atualize o script de start e a documentação do projeto.

### 3.4 Validar

1. **Boot**: suba a aplicação pelo comando real de boot e confirme que inicia sem erro.
2. **Endpoints**: exercite todas as rotas do inventário e compare com a linha de base. Divergência que não seja mudança intencional de contrato é regressão.
3. **Anti-patterns**: repita as buscas da Fase 2 para os findings marcados como resolvidos e confirme que os sinais sumiram.
4. Se algo falhar, corrija e valide de novo — no máximo 3 ciclos. Persistindo a falha, pare e relate exatamente o que não passou.
5. Encerre qualquer processo iniciado e restaure o backup dos dados locais.

### 3.5 Relatar

Imprima o resumo final neste formato:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore de diretórios resultante, uma linha de papel por arquivo>

## Findings
| ID | Severity | Pattern | Status | Fix |
<uma linha por finding: resolved | deferred (motivo)>
Resolved: <n>/<total> | Deferred: <n>

## Intentional contract changes
<lista, ou "None">

## Validation
  ✓|✗ Application boots without errors        (<comando>)
  ✓|✗ All endpoints respond correctly         (<n>/<total> rotas)
  ✓|✗ Anti-patterns resolved                  (<n> resolved, <n> deferred)

| Method | Route | Baseline | After | Result |
<uma linha por rota>
================================
```

Termine com uma linha sobre o que o humano deve fazer em seguida (revisar o diff, definir as variáveis de ambiente do `.env.example`, commitar).
