import pandas as pd
import streamlit as st

from futebol import metricas
from futebol.visualizacoes import CORES_TIMES

COLUNAS_EVENTOS = {
    "period": "Período", "minuto": "Minuto", "team": "Time", "player": "Jogador", "tipo": "Tipo",
    "resultado": "Resultado", "pass_recipient": "Receptor", "xg": "xG", "x": "x", "y": "y",
    "x_fim": "x final", "y_fim": "y final", "play_pattern": "Origem da jogada",
}
CSS = """
<style>
[data-testid="stMetric"] {
    background: var(--fundo-cartao, #f0efec);
    border-left: 4px solid var(--cor-destaque, #2a78d6);
    border-radius: 6px;
    padding: 8px 12px;
}
[data-testid="stMetricValue"] { font-size: 1.6rem; }
.st-key-time_casa [data-testid="stMetric"] { --cor-destaque: #2a78d6; }
.st-key-time_fora [data-testid="stMetric"] { --cor-destaque: #eb6834; }
.st-key-decisivos [data-testid="stMetric"] { --cor-destaque: #0ca30c; }
</style>
"""


def aplicar_estilo():
    st.markdown(CSS, unsafe_allow_html=True)


def cabecalho(ctx):
    p = ctx.partida
    st.caption(f"{ctx.competicao} · temporada {ctx.temporada} · {p['competition_stage']}")
    casa, placar, fora = st.columns([3, 2, 3], vertical_alignment="center")
    casa.markdown(f"<h2 style='text-align:right;color:{CORES_TIMES[0]}'>{p['home_team']}</h2>", unsafe_allow_html=True)
    fora.markdown(f"<h2 style='color:{CORES_TIMES[1]}'>{p['away_team']}</h2>", unsafe_allow_html=True)
    placar.markdown(f"<p style='font-size:2.6rem;font-weight:700;text-align:center;margin:0'>"
                    f"{p['home_score']} x {p['away_score']}</p>", unsafe_allow_html=True)
    penaltis = metricas.placar_penaltis(ctx.eventos)
    if penaltis:
        placar.caption(
            f"Pênaltis: {penaltis.get(p['home_team'], 0)} x {penaltis.get(p['away_team'], 0)}",
            text_alignment="center",
        )
    st.caption(f"📅 {p['match_date']} · 🏟️ {p['stadium'] or 'estádio não informado'} · "
               f"🧑‍⚖️ {p['referee'] or 'árbitro não informado'}")


def tabela_eventos(eventos):
    df = eventos.assign(
        minuto=eventos["minute"].astype(str) + ":" + eventos["second"].astype(str).str.zfill(2),
        xg=eventos["xg"].where(eventos["type"] == "Shot"),
    )
    return df[list(COLUNAS_EVENTOS)].rename(columns=COLUNAS_EVENTOS)


def config_eventos():
    return {
        "xG": st.column_config.ProgressColumn("xG", min_value=0.0, max_value=1.0, format="%.2f"),
        "x": st.column_config.NumberColumn(format="%.1f"),
        "y": st.column_config.NumberColumn(format="%.1f"),
        "x final": st.column_config.NumberColumn(format="%.1f"),
        "y final": st.column_config.NumberColumn(format="%.1f"),
    }


def botao_csv(df, nome, rotulo="Baixar CSV", chave=None):
    st.download_button(
        rotulo, df.to_csv(index=False).encode("utf-8"), file_name=nome, mime="text/csv",
        icon=":material/download:", key=chave, on_click="ignore",
    )


def opcoes_jogadores(ctx, time=None):
    tab = ctx.jogadores if time is None else ctx.jogadores[ctx.jogadores["time"] == time]
    return tab.sort_values("indice", ascending=False).index.tolist()


def rotulo_jogador(ctx):
    return lambda nome: f"{nome} ({ctx.jogadores.loc[nome, 'time']})"


def filtrar_minutos(df, intervalo):
    return df[(df["tempo"] >= intervalo[0]) & (df["tempo"] <= intervalo[1])]


def formatar_numero(v, casas=0):
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".") if pd.notna(v) else "-"
