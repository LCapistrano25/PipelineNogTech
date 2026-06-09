"""
Gera os dados agregados consumidos pelo Dashboard de BI (dashboard/index.html).

Lê o resultado final do Data Lake (Parquet particionado por ano/mes), calcula KPIs
e séries agregadas, e grava em `dashboard/data.js` no formato:

    window.__DASHBOARD_DATA__ = { ... };

Esse formato (arquivo .js que popula uma variável global) permite abrir o dashboard
diretamente via file:// sem esbarrar em restrições de CORS do fetch().

Uso (dentro do ambiente do projeto):
    uv run python dashboard/generate_dashboard_data.py
    # ou via Docker:
    docker compose run --rm --no-deps etl-pipeline uv run python dashboard/generate_dashboard_data.py
"""

import json
import logging
import os
from datetime import datetime, timezone

import pandas as pd

from config import settings

logger = logging.getLogger(__name__)

OUTPUT_JS = os.path.join(settings.BASE_DIR, "dashboard", "data.js")


def _round(value, ndigits=2):
    """Arredonda com segurança, tratando NaN/None."""
    if value is None or pd.isna(value):
        return 0
    return round(float(value), ndigits)


def build_payload(df: pd.DataFrame) -> dict:
    # Normaliza tipos vindos do Parquet (ano/mes chegam como 'category').
    df = df.copy()
    df["ano"] = df["ano"].astype(int)
    df["mes"] = df["mes"].astype(int)
    df["valor_brl"] = pd.to_numeric(df["valor_brl"], errors="coerce").fillna(0.0)
    df["venda_em_feriado"] = df["venda_em_feriado"].astype(bool)
    df["periodo"] = df["ano"].astype(str) + "-" + df["mes"].astype(str).str.zfill(2)

    total_transacoes = int(len(df))
    receita_total = float(df["valor_brl"].sum())
    alunos_unicos = int(df["cpf_aluno"].nunique())

    com_engajamento = int(df["horas_assistidas"].notna().sum())
    cep_resolvido = int(df["cidade"].notna().sum())

    # Receita proveniente de quem NÃO tem consumo registrado (risco de churn).
    receita_sem_consumo = float(df.loc[df["horas_assistidas"].isna(), "valor_brl"].sum())

    kpis = {
        "totalTransacoes": total_transacoes,
        "receitaTotal": _round(receita_total),
        "ticketMedio": _round(receita_total / total_transacoes if total_transacoes else 0),
        "alunosUnicos": alunos_unicos,
        "pctVendasFeriado": _round(100 * df["venda_em_feriado"].mean() if total_transacoes else 0),
        "npsMedio": _round(df["nps_score"].mean()),
        "taxaMatchEngajamento": _round(100 * com_engajamento / total_transacoes if total_transacoes else 0),
        "totalEstados": int(df["estado"].nunique()),
        "totalCidades": int(df["cidade"].nunique()),
        # "Estão consumindo?" — receita em risco (pagantes sem engajamento registrado)
        "receitaSemConsumo": _round(receita_sem_consumo),
        "pctReceitaSemConsumo": _round(100 * receita_sem_consumo / receita_total if receita_total else 0),
    }

    # --- Receita e volume por mês (ordenado cronologicamente) ---
    por_mes = (
        df.groupby("periodo")
        .agg(receita=("valor_brl", "sum"), transacoes=("id_transacao", "count"))
        .reset_index()
        .sort_values("periodo")
    )
    receita_por_mes = [
        {
            "periodo": r["periodo"],
            "receita": _round(r["receita"]),
            "transacoes": int(r["transacoes"]),
        }
        for _, r in por_mes.iterrows()
    ]

    # --- Receita por plano ---
    por_plano = (
        df.groupby("plano_adquirido")
        .agg(receita=("valor_brl", "sum"), transacoes=("id_transacao", "count"))
        .reset_index()
        .sort_values("receita", ascending=False)
    )
    receita_por_plano = [
        {
            "plano": str(r["plano_adquirido"]),
            "receita": _round(r["receita"]),
            "transacoes": int(r["transacoes"]),
            "ticketMedio": _round(r["receita"] / r["transacoes"] if r["transacoes"] else 0),
        }
        for _, r in por_plano.iterrows()
    ]

    # --- Receita/volume por estado (UF) ---
    por_estado = (
        df.dropna(subset=["estado"])
        .groupby("estado")
        .agg(receita=("valor_brl", "sum"), transacoes=("id_transacao", "count"))
        .reset_index()
        .sort_values("receita", ascending=False)
    )
    estados = [
        {
            "estado": str(r["estado"]),
            "receita": _round(r["receita"]),
            "transacoes": int(r["transacoes"]),
            "ticketMedio": _round(r["receita"] / r["transacoes"] if r["transacoes"] else 0),
        }
        for _, r in por_estado.iterrows()
    ]

    # --- Top 10 cidades por receita ---
    por_cidade = (
        df.dropna(subset=["cidade"])
        .groupby(["cidade", "estado"])
        .agg(receita=("valor_brl", "sum"), transacoes=("id_transacao", "count"))
        .reset_index()
        .sort_values("receita", ascending=False)
        .head(10)
    )
    top_cidades = [
        {
            "cidade": str(r["cidade"]),
            "estado": str(r["estado"]),
            "receita": _round(r["receita"]),
            "transacoes": int(r["transacoes"]),
        }
        for _, r in por_cidade.iterrows()
    ]

    # --- Distribuição de NPS ---
    nps = df["nps_score"].dropna().astype(int)
    nps_counts = nps.value_counts().sort_index()
    nps_distrib = [{"score": int(s), "count": int(c)} for s, c in nps_counts.items()]

    # --- Feriado vs dia comum ---
    feriado_grp = df.groupby("venda_em_feriado").agg(
        transacoes=("id_transacao", "count"), receita=("valor_brl", "sum")
    )
    feriado = []
    for flag, label in [(True, "Feriado"), (False, "Dia comum")]:
        if flag in feriado_grp.index:
            row = feriado_grp.loc[flag]
            feriado.append(
                {"label": label, "transacoes": int(row["transacoes"]), "receita": _round(row["receita"])}
            )
        else:
            feriado.append({"label": label, "transacoes": 0, "receita": 0})

    # --- Engajamento por mês (médias) ---
    eng = (
        df.groupby("periodo")
        .agg(
            horasMedia=("horas_assistidas", "mean"),
            npsMedio=("nps_score", "mean"),
            ticketsMedia=("tickets_suporte", "mean"),
        )
        .reset_index()
        .sort_values("periodo")
    )
    engajamento_por_mes = [
        {
            "periodo": r["periodo"],
            "horasMedia": _round(r["horasMedia"]),
            "npsMedio": _round(r["npsMedio"]),
            "ticketsMedia": _round(r["ticketsMedia"]),
        }
        for _, r in eng.iterrows()
    ]

    # --- QUEM PAGA: recorrência de compra (transações por aluno) ---
    compras_por_aluno = df.groupby("cpf_aluno")["id_transacao"].count()
    recorrencia = [
        {"faixa": "1 compra", "alunos": int((compras_por_aluno == 1).sum())},
        {"faixa": "2 compras", "alunos": int((compras_por_aluno == 2).sum())},
        {"faixa": "3+ compras", "alunos": int((compras_por_aluno >= 3).sum())},
    ]

    # --- QUEM PAGA: top alunos por receita (CPF já anonimizado) ---
    por_aluno = (
        df.groupby("cpf_aluno")
        .agg(
            receita=("valor_brl", "sum"),
            compras=("id_transacao", "count"),
            horasMedia=("horas_assistidas", "mean"),
            npsMedio=("nps_score", "mean"),
        )
        .reset_index()
        .sort_values("receita", ascending=False)
        .head(8)
    )
    top_alunos = [
        {
            "cpf": str(r["cpf_aluno"]),
            "receita": _round(r["receita"]),
            "compras": int(r["compras"]),
            # None (→ "—" no dashboard) quando o aluno não tem consumo registrado
            "horasMedia": None if pd.isna(r["horasMedia"]) else _round(r["horasMedia"]),
            "npsMedio": None if pd.isna(r["npsMedio"]) else _round(r["npsMedio"]),
        }
        for _, r in por_aluno.iterrows()
    ]

    # --- ESTÃO CONSUMINDO? Cruzamento pagamento x consumo, por plano ---
    eng_plano = (
        df.groupby("plano_adquirido")
        .agg(
            transacoes=("id_transacao", "count"),
            consumindo=("horas_assistidas", "count"),  # count ignora NaN
            horasMedia=("horas_assistidas", "mean"),
            npsMedio=("nps_score", "mean"),
        )
        .reset_index()
        .sort_values("transacoes", ascending=False)
    )
    engajamento_por_plano = [
        {
            "plano": str(r["plano_adquirido"]),
            "pctConsumindo": _round(100 * r["consumindo"] / r["transacoes"] if r["transacoes"] else 0),
            "horasMedia": _round(r["horasMedia"]),
            "npsMedio": _round(r["npsMedio"]),
            "transacoes": int(r["transacoes"]),
        }
        for _, r in eng_plano.iterrows()
    ]

    # --- ESTÃO CONSUMINDO? Visão consolidada pagantes ativos x inativos ---
    consumo = [
        {"label": "Consumindo a plataforma", "transacoes": com_engajamento, "color": "#10b981"},
        {"label": "Sem consumo registrado", "transacoes": total_transacoes - com_engajamento, "color": "#ef4444"},
    ]

    enriquecimento = {
        "cepResolvido": cep_resolvido,
        "cepNaoResolvido": total_transacoes - cep_resolvido,
        "comEngajamento": com_engajamento,
        "semEngajamento": total_transacoes - com_engajamento,
    }

    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "kpis": kpis,
        "receitaPorMes": receita_por_mes,
        "receitaPorPlano": receita_por_plano,
        "recorrencia": recorrencia,
        "topAlunos": top_alunos,
        "porEstado": estados,
        "topCidades": top_cidades,
        "npsDistrib": nps_distrib,
        "feriado": feriado,
        "engajamentoPorMes": engajamento_por_mes,
        "engajamentoPorPlano": engajamento_por_plano,
        "consumo": consumo,
        "enriquecimento": enriquecimento,
    }


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

    data_lake = settings.ANONYMIZED_TRANSACTIONS
    if not os.path.exists(data_lake):
        raise FileNotFoundError(
            f"Data Lake não encontrado em {data_lake}. Execute o pipeline antes (python main.py)."
        )

    logger.info("Lendo Data Lake de %s", data_lake)
    df = pd.read_parquet(data_lake)
    logger.info("Carregadas %d linhas / %d colunas", len(df), len(df.columns))

    payload = build_payload(df)

    os.makedirs(os.path.dirname(OUTPUT_JS), exist_ok=True)
    with open(OUTPUT_JS, "w", encoding="utf-8") as f:
        f.write("// Gerado automaticamente por dashboard/generate_dashboard_data.py — não editar à mão.\n")
        f.write("window.__DASHBOARD_DATA__ = ")
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write(";\n")

    logger.info("Dados do dashboard gravados em %s", OUTPUT_JS)


if __name__ == "__main__":
    main()
