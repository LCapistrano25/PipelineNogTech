# PipelineNogTech

Pipeline ETL para consolidar dados de transacoes e engajamento da NogTech. O fluxo usa Python, Luigi e Docker para extrair arquivos locais, enriquecer informacoes com a BrasilAPI, anonimizar dados sensiveis e gravar o resultado final em Parquet.

> **Documentacao detalhada:** para o passo a passo de como o Luigi orquestra cada etapa (construcao do DAG, idempotencia, scheduler e resiliencia), veja [documents/FLUXO_LUIGI.md](documents/FLUXO_LUIGI.md). Para visualizar o resultado final, veja o [Dashboard de BI](#dashboard-de-bi).

## Inicializacao do ambiente

Para subir o ambiente pela primeira vez, ou reconstruir a imagem:

```bash
docker-compose up --build
```

Para execucoes seguintes:

```bash
docker-compose up
```

Para encerrar os containers:

```bash
docker-compose down
```

Em ambientes com Docker Compose V2, os mesmos comandos podem ser executados com `docker compose`.

## Interfaces visuais

O `docker-compose.yml` publica duas interfaces visuais:

- Luigi Central Scheduler: http://localhost:8082
- Dashboard de BI: http://localhost:8000

O servico `dashboard` so sobe **apos o pipeline terminar com sucesso**
(`service_completed_successfully`): ele gera o `dashboard/data.js` a partir do
Data Lake e serve a pagina automaticamente. Assim, ao rodar `docker-compose up`,
a interface ja reflete o resultado da execucao — basta acessar
http://localhost:8000.

## Saidas geradas

Durante a execucao, o pipeline grava arquivos intermediarios e finais nas seguintes pastas:

- `output/loaded`: dados extraidos e convertidos para Parquet.
- `output/processed`: dados padronizados, enriquecidos e anonimizados.
- `output/transformed`: base consolidada antes da carga final.
- `output/final/data_lake`: destino final em Parquet particionado.
- `logs/pipeline.log`: log da execucao.

## Dashboard de BI

A pasta [dashboard/](dashboard/) contem uma pagina de Business Intelligence (React + Recharts, sem build) que apresenta a saida final do pipeline: receita, geografia, calendario (feriados) e engajamento dos alunos.

O dashboard le os dados agregados de `dashboard/data.js`, gerado a partir do Data Lake.

### Via Docker (automatico, recomendado)

Nao e preciso nenhum passo manual: o servico `dashboard` do compose aguarda o
pipeline concluir, gera o `data.js` e serve a pagina. Basta subir o ambiente e
acessar **http://localhost:8000**:

```bash
docker-compose up --build
```

### Manualmente (sem Docker)

Apos executar o pipeline, gere os dados e sirva a pasta:

```bash
# 1. Gera os dados agregados a partir de output/final/data_lake
uv run python -m dashboard.generate_dashboard_data

# 2. Serve a pasta (servidor estatico evita bloqueio de CORS ao carregar data.js)
python3 -m http.server 8000 --directory dashboard
```

Acesse **http://localhost:8000**. Detalhes em [dashboard/README.md](dashboard/README.md).

## Idempotencia e tratamento de falhas

A idempotencia combina a orquestracao do Luigi com a estrategia de gravacao dos dados. Cada etapa declara seu `LocalTarget`, permitindo que o Luigi reconheca tasks ja concluidas e evite reprocessamento desnecessario. Na carga final, os dados sao gravados em Parquet particionado por `ano` e `mes`, com comportamento de sobrescrita/ignore para reduzir risco de duplicidade em reexecucoes do mesmo lote.

As consultas externas tambem sao protegidas por cache local em JSON: CEPs consultados sao armazenados em `databases/cep_cache.json`, e feriados sao armazenados por ano em `databases/holiday_cache.json`. Isso evita chamadas repetidas para a BrasilAPI e torna novas execucoes mais previsiveis.

O tratamento de falhas fica centralizado no Luigi e nos logs da aplicacao. Quando uma task falha, suas dependentes nao prosseguem, e o erro fica visivel no scheduler, no console e em `logs/pipeline.log`. As integracoes com a BrasilAPI usam timeout e retry para respostas `429` e erros `5xx`; falhas de consulta sao registradas e retornam ausencia de enriquecimento quando aplicavel.

## Validacao

Para validar a configuracao do compose:

```bash
docker-compose config
```

Depois de subir o ambiente, acesse o scheduler do Luigi em http://localhost:8082 para acompanhar o estado das tasks.
