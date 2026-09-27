"""
Metrics Dashboard — reads metrics.jsonl directly (same file evaluator.py
writes to) and visualizes cost, latency, cache-hit rates, and path
distribution over time.

Streamlit auto-discovers this as a second page since it's in ui/pages/.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from app.analysis.evaluator import evaluator
from app.config import cfg

st.set_page_config(page_title="Spark Insight — Metrics", layout="wide")
st.title("📊 Query Metrics Dashboard")


@st.cache_data(ttl=10)
def load_metrics() -> pd.DataFrame:
    log_path = Path(cfg.metrics_log_path)
    if not log_path.exists():
        return pd.DataFrame()

    rows = []
    with open(log_path) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


df = load_metrics()

if df.empty:
    st.info("No queries logged yet. Ask something in the main app first.")
    st.stop()

all_time = evaluator.get_all_time_summary()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Queries", all_time.get("total_queries_all_time", len(df)))
col2.metric("Total Cost", f"${all_time.get('total_cost_all_time_usd', 0):.6f}")
col3.metric("Avg Cost/Query", f"${all_time.get('avg_cost_per_query_usd', 0):.6f}")
llm_avoided_pct = round(100 * (df["path"] != "llm").sum() / len(df), 1)
col4.metric("LLM Avoided", f"{llm_avoided_pct}%")

st.divider()

col1, col2, col3 = st.columns(3)
col1.metric("Latency p50", f"{df['latency_ms'].median():.0f} ms")
col2.metric("Latency p95", f"{df['latency_ms'].quantile(0.95):.0f} ms")
col3.metric("Avg Confidence", f"{df['confidence'].mean():.2f}")

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("Path Distribution")
    st.bar_chart(df["path"].value_counts())

with right:
    st.subheader("Cache Hit Rates")
    hit_rates = pd.Series(
        {
            "Query Cache": df["query_cache_hit"].mean(),
            "Embedding Cache": df["embedding_cache_hit"].mean(),
            "LLM Cache": df["llm_cache_hit"].mean(),
        }
    )
    st.bar_chart(hit_rates)

st.subheader("Latency Over Time")
st.line_chart(df.set_index("timestamp")["latency_ms"])

st.subheader("Cost Over Time (cumulative)")
df_sorted = df.sort_values("timestamp")
df_sorted["cumulative_cost"] = df_sorted["total_cost_usd"].cumsum()
st.line_chart(df_sorted.set_index("timestamp")["cumulative_cost"])

st.divider()

with st.expander("Raw query log (most recent first)"):
    st.dataframe(
        df.sort_values("timestamp", ascending=False)[
            ["timestamp", "path", "confidence", "top_similarity", "latency_ms",
             "total_cost_usd", "query_cache_hit", "embedding_cache_hit", "llm_cache_hit"]
        ],
        use_container_width=True,
    )