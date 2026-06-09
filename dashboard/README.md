# Dashboard de BI — NogTech

Página de Business Intelligence (React + Recharts) que apresenta a saída final do
pipeline ETL: receita, geografia, calendário (feriados) e engajamento dos alunos.

## Arquivos

| Arquivo | Função |
| --- | --- |
| `index.html` | A página do dashboard. React, Recharts e Babel são carregados via CDN — **não há build**. |
| `generate_dashboard_data.py` | Lê o Data Lake (`output/final/data_lake`) e gera `data.js` com os dados agregados. |
| `data.js` | Dados agregados (`window.__DASHBOARD_DATA__`). **Gerado automaticamente** — não editar à mão. |

## Como usar

1. **Execute o pipeline** primeiro (ver [../README.md](../README.md)), para que
   `output/final/data_lake` exista.

2. **Gere os dados agregados** (rode a partir da raiz do projeto):

   ```bash
   uv run python -m dashboard.generate_dashboard_data
   # ou via Docker:
   docker compose run --rm --no-deps etl-pipeline uv run python -m dashboard.generate_dashboard_data
   ```

3. **Sirva a pasta** e abra no navegador (um servidor estático evita o bloqueio
   de CORS ao carregar `data.js`):

   ```bash
   python -m http.server -d dashboard 8000
   ```

   Acesse **http://localhost:8000**.

## O que é exibido

O painel é organizado para responder, em uma única visão, às quatro perguntas da
diretoria, além de um resumo executivo (KPIs) no topo — incluindo a **Receita em
risco** (pagantes sem consumo registrado):

| Seção | Pergunta da diretoria | Conteúdo |
| --- | --- | --- |
| **Quem paga** | Quem está pagando pelos cursos? | Receita por plano, ticket médio e volume por plano, recorrência de compra e tabela dos maiores pagantes (CPF anonimizado, com flag de "sem consumo"). |
| **De onde vem** | De onde vêm (geograficamente)? | Receita por estado (UF) com ticket médio e top cidades por receita. |
| **Quando compra** | Em quais datas (incluindo feriados)? | Receita e volume por mês e vendas em feriado × dia comum (com ticket médio comparado). |
| **Estão consumindo?** | Estão realmente consumindo a plataforma? | Cruzamento pagamento × consumo: pagamentos com/sem engajamento, % que assiste por plano, engajamento médio por mês e distribuição de NPS. |
| **Qualidade** | (saúde do pipeline) | Cobertura do enriquecimento de CEP via BrasilAPI. |
