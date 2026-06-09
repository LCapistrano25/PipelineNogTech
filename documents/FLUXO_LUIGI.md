# Fluxo de Execução do Pipeline (Luigi) — Passo a Passo

Este documento descreve **o que o Luigi faz**, como o pipeline ETL da NogTech é
orquestrado e o que acontece em **cada etapa de execução**, do disparo inicial
até a gravação final no Data Lake.

> Para uma visão geral do projeto e comandos, veja o [README.md](../README.md).
> Para visualizar o resultado final, veja o [dashboard de BI](../dashboard/index.html).

---

## 1. Conceitos do Luigi usados aqui

O Luigi é um orquestrador de **grafos de tarefas (DAG)**. Em vez de um script
linear, o pipeline é modelado como um conjunto de tarefas que declaram suas
dependências. Três métodos definem cada tarefa (`luigi.Task`):

| Método | Papel no projeto |
| --- | --- |
| `requires()` | Lista as tarefas que precisam terminar **antes** desta começar. É o que forma o DAG. |
| `run()` | A lógica de fato: lê o Parquet da etapa anterior, transforma o DataFrame e grava o resultado. |
| `output()` | Retorna um `luigi.LocalTarget` (um arquivo/diretório). É o "checkpoint" da tarefa. |

**Como o Luigi decide o que rodar:** antes de executar uma tarefa, ele verifica
se o `output()` dela **já existe**. Se existir, a tarefa é considerada concluída
e é **pulada** (isso é a base da idempotência — ver seção 4). Se não existir, o
Luigi primeiro resolve as dependências de `requires()` e só então executa o
`run()`.

O **agendamento** (executar tarefas na ordem certa, respeitando dependências e
paralelismo) é feito por um *scheduler* — local ou central (ver seção 5).

---

## 2. Ponto de entrada e construção do DAG

O pipeline é disparado por [main.py](../main.py):

```python
luigi.build([LoadDataLakeTask()], local_scheduler=PIPELINE_LOCAL_SCHEDULER)
```

Repare que **apenas uma tarefa é nomeada**: `LoadDataLakeTask` (a etapa final de
carga). O Luigi monta o grafo completo **de trás para frente**, seguindo
recursivamente o `requires()` de cada tarefa até chegar nas extrações (que não
dependem de nada). Ou seja: você pede o resultado final e o Luigi descobre
sozinho tudo que precisa ser feito antes.

Antes do `build`, o `main.py` também configura o **logging estruturado**
(console + arquivo `logs/pipeline.log`), conforme o nível definido em `LOG_LEVEL`.

### O grafo resultante

```
                    [ Fonte CSV ]                                  [ Fonte JSON ]
                         │                                              │
            1. ExtractTransactionsTask                     6. ExtractEngagementTask
                         │                                              │
            2. TransformTransactionsTask                    7. TransformEngagementTask
                         │                                              │
            3. EnrichTransactionsAddressTask  (BrasilAPI CEP)           │
                         │                                              │
            4. EnrichTransactionsHolidayTask  (BrasilAPI Feriados)      │
                         │                                              │
                         └──────────────┬───────────────────────────────┘
                                        ▼
                          8. TransformEnrichedDataTask   (LEFT JOIN)
                                        │
                          9. TransactionAnonymizationTask  (LGPD)
                                        │
                         10. LoadDataLakeTask   (Parquet particionado ano/mês)
```

São **dois ramos independentes** (transações e engajamento) que o Luigi pode
processar e que convergem no JOIN (etapa 8).

---

## 3. As etapas de execução, uma a uma

Toda tarefa segue o mesmo padrão: lê o Parquet de entrada via
`self.input()[i].path`, processa um `DataFrame` do pandas e grava com
`save_df_to_parquet(...)`. Os caminhos de cada arquivo são constantes
centralizadas em [config/settings.py](../config/settings.py).

### Ramo das transações

#### Etapa 1 — `ExtractTransactionsTask` (Extract)
- **Arquivo:** [pipelines/extract/extract_transactions.py](../pipelines/extract/extract_transactions.py)
- **Entrada:** `databases/transacoes_nogtech.csv` (encoding `latin-1`, delimitador `;`).
- **Faz:** lê o CSV bruto e o converte para Parquet, sem transformar. Valida a
  existência do arquivo (`FileNotFoundError` se faltar).
- **Saída:** `output/loaded/transactions_nogtech.parquet`.

#### Etapa 2 — `TransformTransactionsTask` (Transform)
- **Arquivo:** [pipelines/transform/transform_transactions.py](../pipelines/transform/transform_transactions.py)
- **Faz a padronização e limpeza:**
  - `data_transacao` → datetime (lidando com múltiplos formatos via `parse_date`); deriva colunas `mes` e `ano`.
  - `cpf_aluno` → formato canônico `000.000.000-00` (`format_cpf`). **Isso ocorre antes da anonimização**, como exige o requisito.
  - `valor_brl` → float (`format_float`, trata vírgula decimal).
  - `cep_cobranca` → apenas dígitos (`format_cep`).
  - **Regra de negócio:** preenche `plano_adquirido` nulo inferindo o plano a partir do `valor_brl` (mapa valor→plano construído a partir das linhas conhecidas).
- **Saída:** `output/processed/transactions.parquet`.

#### Etapa 3 — `EnrichTransactionsAddressTask` (Transform / Enriquecimento)
- **Arquivo:** [pipelines/transform/enrich_transactions_address.py](../pipelines/transform/enrich_transactions_address.py)
- **Faz:** para cada CEP **único**, consulta a [BrasilAPI de CEP](https://brasilapi.com.br/api/cep/v2/) via `CepEnrichmentService` e adiciona as colunas `bairro`, `cidade`, `estado`.
- **Cache obrigatório:** antes de chamar a API, consulta `databases/cep_cache.json`. CEPs já vistos não são consultados de novo (ver seção 6). CEPs que a API não resolve ficam com endereço nulo — a transação é mantida.
- **Saída:** `output/processed/transactions_enriched_address.parquet`.

#### Etapa 4 — `EnrichTransactionsHolidayTask` (Transform / Enriquecimento)
- **Arquivo:** [pipelines/transform/enrich_transactions_holiday.py](../pipelines/transform/enrich_transactions_holiday.py)
- **Faz:** para cada **ano** presente nos dados, consulta a [BrasilAPI de Feriados](https://brasilapi.com.br/api/feriados/v1/) via `HolidayEnrichmentService` e cria a coluna booleana `venda_em_feriado` (se `data_transacao` cai num feriado nacional).
- **Cache obrigatório:** feriados são cacheados **por ano** em `databases/holiday_cache.json` — **uma única chamada por ano** atende todas as transações daquele período.
- **Saída:** `output/processed/transactions_enriched_holiday.parquet`.

### Ramo do engajamento (independente, roda em paralelo)

#### Etapa 6 — `ExtractEngagementTask` (Extract)
- **Arquivo:** [pipelines/extract/extract_engagement.py](../pipelines/extract/extract_engagement.py)
- **Entrada:** `databases/engajamento_alunos.json` (utf-8).
- **Faz:** lê o JSON e converte para Parquet, sem transformar.
- **Saída:** `output/loaded/engagement_students.parquet`.

#### Etapa 7 — `TransformEngagementTask` (Transform)
- **Arquivo:** [pipelines/transform/transform_engagement.py](../pipelines/transform/transform_engagement.py)
- **Faz:** converte `mes_referencia` (`YYYY-MM`) em datetime e deriva `mes`/`ano`; normaliza `horas_assistidas` e `nps_score` (float) e `cpf_aluno` (mesmo formato canônico da etapa 2, garantindo chave de JOIN consistente).
- **Saída:** `output/processed/engagement.parquet`.

### Convergência, anonimização e carga

#### Etapa 8 — `TransformEnrichedDataTask` (Transform / JOIN)
- **Arquivo:** [pipelines/transform/transform_engagement_transactions.py](../pipelines/transform/transform_engagement_transactions.py)
- **Depende de:** etapas 4 **e** 7 (é onde os dois ramos se encontram).
- **Faz:** `LEFT JOIN` entre transações enriquecidas e engajamento, usando a chave composta `['cpf_aluno', 'mes', 'ano']`. Transações **sem** engajamento correspondente são mantidas, com os campos de engajamento nulos. Valida a presença das colunas-chave antes do merge e loga quantos registros tiveram match.
- **Saída:** `output/transformed/enriched_engagement_transactions.parquet`.

#### Etapa 9 — `TransactionAnonymizationTask` (Transform / LGPD)
- **Arquivo:** [pipelines/transform/transaction_anonymization.py](../pipelines/transform/transaction_anonymization.py)
- **Faz (conformidade LGPD):**
  - **Mascara o CPF:** `123.456.789-00` → `***.456.789-**` (só os 6 dígitos centrais ficam visíveis).
  - **Remove a coluna `nome_aluno`** inteira (identificador direto — não basta mascarar).
- **Saída:** `output/processed/transactions_anonymized.parquet`.

#### Etapa 10 — `LoadDataLakeTask` (Load)
- **Arquivo:** [pipelines/load/load_data_lake.py](../pipelines/load/load_data_lake.py)
- **Faz:** grava o resultado final em Parquet **particionado por `ano/mes`** simulando um Data Lake.
- **Saída:** diretório `output/final/data_lake/ano=YYYY/mes=M/...parquet`.

Ao final, o `main.py` registra "Pipeline finalizada com sucesso!" em
`logs/pipeline.log`.

---

## 4. Idempotência (reexecuções sem duplicar dados)

A estratégia adotada é a **Opção B do requisito** — particionamento por data com
sobrescrita — combinada com o mecanismo de *targets* do Luigi:

1. **Targets do Luigi:** como cada etapa só roda se seu `output()` não existir,
   reexecutar o pipeline **pula** todas as etapas cujos Parquets já estão no
   disco. Nada é reprocessado à toa.
2. **Carga particionada:** na etapa final, `save_df_to_parquet(...)` usa
   `existing_data_behavior="overwrite_or_ignore"` com partições `ano/mes`
   (ver [infrastructure/utils/file_utils.py](../infrastructure/utils/file_utils.py)).
   Reprocessar o mesmo lote **sobrescreve** a partição em vez de acumular
   duplicatas.

> **Para forçar o reprocessamento de uma etapa**, apague o arquivo/diretório de
> saída dela dentro de `output/` (e, se quiser refazer as consultas externas,
> apague também os `databases/*_cache.json`).

---

## 5. O scheduler: local vs. central

A flag `PIPELINE_LOCAL_SCHEDULER` (variável de ambiente
`LUIGI_LOCAL_SCHEDULER`, lida em [config/settings.py](../config/settings.py))
decide como o `main.py` agenda as tarefas:

- **`True` (padrão no código):** usa um scheduler **em processo**. Roda com
  `uv run python main.py` sem precisar de Docker nem interface web.
- **`False` (definido no `docker-compose.yml` e no `.env.config`):** conecta ao
  **Luigi Central Scheduler**, um serviço separado (container `luigi-scheduler`,
  binário `luigid`) acessível em **http://localhost:8082** (host/porta em
  [luigi.cfg](../luigi.cfg)). É ele que fornece a **observabilidade** exigida:
  grafo de execução, histórico e tempo de cada nó.

No `docker-compose.yml` o serviço `etl-pipeline` espera o `luigi-scheduler` ficar
saudável (`healthcheck`) antes de rodar `main.py`, garantindo que a interface já
esteja no ar quando o pipeline começa.

---

## 6. Resiliência e tratamento de falhas

**Cache de API (evita chamadas repetidas):** os serviços de enriquecimento
consultam um cache em JSON antes de ir à rede. CEPs são cacheados por CEP
(`AddressCache`) e feriados por ano (`HolidayCache`), ambos em
[infrastructure/cache/](../infrastructure/cache/). Isso satisfaz o requisito de
"não consultar a API duas vezes para a mesma chave" e torna reexecuções mais
rápidas e previsíveis.

**Retry e timeout na BrasilAPI:** os clientes HTTP
([brasil_api_cep_service.py](../infrastructure/services/cep/brasil_api_cep_service.py)
e o de feriados) usam `urllib3.Retry` com *backoff* exponencial nos status
`429/500/502/503/504`, além de `timeout` configurável (`API_TIMEOUT`/`API_RETRIES`).
Em caso de falha definitiva, a função **loga o erro e retorna `None`/vazio** — o
enriquecimento daquele registro fica ausente, mas **os dados não são corrompidos**
e o pipeline continua.

**Propagação de falhas no Luigi:** se o `run()` de uma tarefa lança exceção, o
Luigi marca a tarefa como `FAILED` e **não executa as tarefas dependentes**. O
erro aparece no scheduler (porta 8082), no console e em `logs/pipeline.log`.
Como nada foi gravado no `output()` da tarefa que falhou, uma reexecução tenta de
novo a partir daquele ponto (as etapas anteriores, já concluídas, são puladas).

---

## 7. Como executar

```bash
# Ambiente completo com scheduler central + interface web (recomendado para demo)
docker-compose up --build      # primeira vez / rebuild
docker-compose up              # execuções seguintes
# Acompanhe em http://localhost:8082

# Execução local com scheduler em processo (sem Docker)
uv run python main.py
```

Depois de executar, gere os dados do dashboard de BI e abra-o:

```bash
uv run python -m dashboard.generate_dashboard_data
python -m http.server -d dashboard 8000   # acesse http://localhost:8000
```
