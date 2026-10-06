# Template do Relatório de Auditoria

Formato obrigatório da saída da Fase 2. O mesmo texto é impresso no terminal e salvo em arquivo. Rótulos e ordem das seções são fixos; o conteúdo vem da auditoria.

## Estrutura

````
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome do diretório do projeto>
Stack:   <linguagem> + <framework> (<banco / acesso a dados>)
Files:   <n> analyzed | ~<n> lines of code
Date:    <AAAA-MM-DD>

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [CRITICAL] F-01 — <nome do anti-pattern>
Pattern: AP-xx
File: <caminho/arquivo.ext>:<linha>[-<linha>][, <linha>-<linha> ...]
Description: <o que está errado, citando o símbolo ou trecho concreto>
Impact: <consequência objetiva para segurança, manutenção, testes ou performance>
Recommendation: <o que fazer> (T-xx)

### [CRITICAL] F-02 — ...

### [HIGH] F-0n — ...

### [MEDIUM] F-0n — ...

### [LOW] F-0n — ...

## Deprecated APIs
| API | File | Deprecated since | Replacement |
|-----|------|------------------|-------------|
| <chamada> | <arquivo>:<linhas> | <versão do runtime/lib> | <equivalente moderno> |

## Proposed Target Structure
```
<árvore de diretórios MVC proposta para este projeto>
```
<1 a 3 linhas: o que muda em relação à estrutura atual e o que é mantido>

================================
Total: <n> findings
================================
````

## Regras de preenchimento

**Cabeçalho**
- `Files` e linhas de código são os mesmos números do resumo da Fase 1.

**Summary**
- A soma das quatro contagens é igual ao `Total` e ao número de blocos `###` em Findings.

**Findings**
- Ordenação: CRITICAL → HIGH → MEDIUM → LOW. Dentro da mesma severidade, pelo ID do catálogo.
- IDs sequenciais `F-01`, `F-02`... na ordem final do relatório.
- `Pattern`: ID do catálogo (`AP-xx`). Use `AP-00` para problema fora do catálogo.
- `File`: caminho relativo à raiz do projeto, com linha ou faixa exata. Várias ocorrências no mesmo arquivo vão separadas por vírgula. Quando o mesmo problema atravessa arquivos, repita a linha `File:` para cada arquivo. Nunca use "vários arquivos", "ao longo do código" ou linha aproximada.
- `Description`: fato observável. Cite o nome da função, a variável ou o literal envolvido. Para segredos, cite o nome da chave e mascare o valor (`'minh…123'`).
- `Impact`: consequência específica deste projeto, não a definição genérica do padrão.
- `Recommendation`: ação concreta e o ID da transformação do playbook (`T-xx`).
- Um finding por padrão por arquivo. Padrão que se repete em vários arquivos como parte do mesmo problema (ex.: a mesma regra duplicada) é um finding com várias linhas `File:`.
- Texto no idioma do usuário; rótulos (`File`, `Description`...) sempre como no template.

**Deprecated APIs**
- A seção existe sempre. Sem ocorrências, substitua a tabela pela linha: `None detected (checked against <runtime e versões verificadas>).`
- Cada linha da tabela corresponde a um finding AP-15 em Findings (um finding pode agrupar várias linhas).

**Proposed Target Structure**
- Árvore conforme as guidelines de MVC, já adaptada ao nível de organização do projeto (N0/N1/N2).
- Em projetos N2, marque o que é mantido, o que é criado e o que é movido.

## Exemplo de finding bem preenchido

```
### [CRITICAL] F-02 — Injeção de SQL
Pattern: AP-02
File: models.py:28, 47-50, 109-111
Description: Queries montadas por concatenação com valores vindos da requisição; em login_usuario (109-111) email e senha entram direto no WHERE.
Impact: Qualquer cliente lê ou altera qualquer tabela; o login é burlável com `' OR '1'='1`.
Recommendation: Substituir por queries parametrizadas com placeholders (T-02).
```

## Exemplo de finding mal preenchido (não fazer)

```
### [HIGH] Código ruim nos models
File: models.py
Description: O arquivo tem vários problemas de qualidade.
Impact: Dificulta a manutenção.
Recommendation: Refatorar.
```

Faltam ID, padrão, linha, o fato concreto, o impacto específico e a ação.

## Linha de confirmação

Depois do bloco `Total`, e fora do relatório salvo, a última linha impressa é:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```
