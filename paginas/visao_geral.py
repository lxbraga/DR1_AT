import streamlit as st

from futebol import estado, interface, metricas

ctx = estado.contexto()
casa, fora = ctx.times

st.title("Quem decidiu a partida?")
st.markdown(
    "Painel com dados abertos da StatsBomb para descobrir **quais jogadores mais influenciaram o resultado** "
    "de uma partida: finalização (gols e xG), criação (assistências, xA e passes-chave), progressão e defesa."
)

# Item 4.2: competição, temporada e partida
with st.container(border=True):
    interface.cabecalho(ctx)

# Item 7: indicadores por time, com delta em relação ao adversário
st.subheader("Estatísticas básicas")
est = metricas.estatisticas_partida(ctx.eventos, ctx.times)
indicadores = [
    ("Gols", "Gols", 0), ("Chutes", "Chutes", 0), ("xG", "xG", 2),
    ("Passes certos", "Passes certos", 0), ("Precisão de passe (%)", "Precisão de passe", 1),
    ("Conversão (%)", "Conversão de chutes", 1),
]
for time, adversario, chave in [(casa, fora, "time_casa"), (fora, casa, "time_fora")]:
    with st.container(key=chave):
        st.markdown(f"**{time}**")
        colunas = st.columns(3) + st.columns(3)
        for coluna, (linha, rotulo, casas) in zip(colunas, indicadores):
            valor, delta = est.loc[linha, time], est.loc[linha, time] - est.loc[linha, adversario]
            sufixo = "%" if "%" in linha else ""
            coluna.metric(
                rotulo, f"{interface.formatar_numero(valor, casas)}{sufixo}",
                delta=f"{interface.formatar_numero(delta, casas)}{sufixo}" if delta else None,
                delta_color="normal", help=f"Diferença em relação a {adversario}",
            )

st.subheader("Quem decidiu?")
top = ctx.jogadores.nlargest(3, "indice")
with st.container(key="decisivos"):
    for coluna, (nome, linha) in zip(st.columns(3), top.iterrows()):
        coluna.metric(
            f"{nome} ({linha['time']})", f"{linha['indice']:.1f}",
            delta=f"{int(linha['gols'])} gols · {int(linha['assistencias'])} assist. · {linha['xg'] + linha['xa']:.2f} xG+xA",
            delta_color="off", delta_arrow="off",
            help="Índice de decisão de 0 a 100. Pesos editáveis na página 'Quem decidiu?'.",
        )

aba_eventos, aba_times, aba_jogadores = st.tabs(
    ["Eventos da partida", "Estatísticas por time", "Jogadores"], key="aba_visao_geral", on_change="rerun")

# Item 4.2 e 6: DataFrame de eventos com filtros e download
with aba_eventos:
    tipos = sorted(ctx.eventos["tipo"].unique())
    padrao_tipos = [t for t in ["Passe", "Chute", "Duelo", "Interceptação", "Drible"] if t in tipos]
    c1, c2, c3 = st.columns([3, 2, 2])
    selecionados = c1.multiselect("Tipos de evento", tipos, key=estado.preparar("ev_tipos", padrao_tipos, tipos),
                                  on_change=estado.salvar, args=("ev_tipos",))
    time_ev = c2.radio("Time", ["Ambos", casa, fora], horizontal=True,
                       key=estado.preparar("ev_time", "Ambos", ["Ambos", casa, fora]),
                       on_change=estado.salvar, args=("ev_time",))
    nomes = ["Todos"] + interface.opcoes_jogadores(ctx, None if time_ev == "Ambos" else time_ev)
    jogador_ev = c3.selectbox("Jogador", nomes, key=estado.preparar("ev_jogador", "Todos", nomes),
                              on_change=estado.salvar, args=("ev_jogador",))
    so_chave = st.checkbox("Somente lances decisivos (gols, chutes, passes-chave e assistências)")

    ev = ctx.eventos[ctx.eventos["tipo"].isin(selecionados)]
    if time_ev != "Ambos":
        ev = ev[ev["team"] == time_ev]
    if jogador_ev != "Todos":
        ev = ev[ev["player"] == jogador_ev]
    if so_chave:
        ev = ev[ev["type"].eq("Shot") | ev["pass_shot_assist"].eq(True) | ev["pass_goal_assist"].eq(True)]

    tabela = interface.tabela_eventos(ev)
    st.caption(f"{len(tabela)} eventos de {len(ctx.eventos)}")
    st.dataframe(tabela, hide_index=True, column_config=interface.config_eventos(), height=380)
    interface.botao_csv(tabela, f"eventos_{ctx.partida['match_id']}.csv", "Baixar eventos filtrados (CSV)")

with aba_times:
    comparaveis = [i for i in est.index if i not in ("Faltas", "Impedimentos")]
    estilo = est.style.highlight_max(axis=1, subset=(comparaveis, slice(None)), color="#cde2fb")
    for linha in est.index:
        formato = "{:.2f}" if linha == "xG" else "{:.1f}" if "%" in linha else "{:.0f}"
        estilo = estilo.format(formato, subset=([linha], slice(None)))
    st.dataframe(estilo, height=560)
    st.caption("Em azul, o time que foi superior em cada estatística (exceto faltas e impedimentos).")

with aba_jogadores:
    colunas = ["time", "minutos", "indice", "gols", "assistencias", "chutes", "xg", "xa", "passes",
               "precisao_passe", "passes_chave", "progressivos", "acoes_defensivas"]
    tab = ctx.jogadores.sort_values("indice", ascending=False)[colunas]
    st.dataframe(
        tab.rename(columns=metricas.ROTULOS | {"time": "Time"}),
        column_config={"Índice de decisão": st.column_config.ProgressColumn(min_value=0, max_value=100,
                                                                            format="%.1f")},
        height=460,
    )
    interface.botao_csv(tab.reset_index(), f"jogadores_{ctx.partida['match_id']}.csv",
                        "Baixar estatísticas dos jogadores (CSV)", chave="csv_jogadores")
