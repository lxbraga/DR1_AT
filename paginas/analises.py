import streamlit as st

from futebol import dados, estado, metricas, visualizacoes as viz

ctx = estado.contexto()
st.title("Quem decidiu a partida?")
st.markdown(
    "O **índice de decisão** (0 a 100) soma as estatísticas de cada jogador normalizadas pelo melhor valor da "
    "partida, com os pesos abaixo. Ajuste os pesos para testar outras definições de \"decidir um jogo\"."
)

# Item 8: formulário de pesos do índice
with st.form("form_pesos"):
    atuais = st.session_state.get("pesos", metricas.PESOS_PADRAO)
    colunas = st.columns(len(metricas.PESOS_PADRAO))
    novos = {
        chave: coluna.slider(metricas.ROTULOS[chave], 0.0, 5.0, float(atuais[chave]), 0.5)
        for coluna, chave in zip(colunas, metricas.PESOS_PADRAO)
    }
    c1, c2 = st.columns([1, 3])
    top_n = c1.number_input("Jogadores no ranking", 3, 25, key=estado.preparar("top_n", 10))
    enviar = st.form_submit_button("Recalcular índice", type="primary", on_click=estado.salvar, args=("top_n",))
if enviar:
    st.session_state["pesos"] = novos
    st.rerun()
if st.button("Restaurar pesos padrão", icon=":material/restart_alt:"):
    st.session_state.pop("pesos", None)
    st.rerun()

pesos = st.session_state.get("pesos", metricas.PESOS_PADRAO)
tab = ctx.jogadores
top = tab.nlargest(int(top_n), "indice")
lider = top.iloc[0]
st.success(f"Pelo índice, quem mais decidiu foi **{top.index[0]}** ({lider['time']}), com {lider['indice']:.1f} pontos.")

aba_ranking, aba_xg, aba_relacoes = st.tabs(
    ["Ranking", "Corrida de xG", "Relações entre estatísticas"], key="aba_analises", on_change="rerun")

# Item 5.2: visualizações com matplotlib e seaborn
with aba_ranking, st.spinner("Calculando o ranking..."):
    contrib = metricas.contribuicoes_por_familia(tab, pesos).loc[top.index]
    viz.exibir(viz.barras_contribuicao(contrib, tab["time"].to_dict()))

with aba_xg, st.spinner("Desenhando a corrida de xG..."):
    viz.exibir(viz.xg_acumulado(metricas.serie_xg_acumulado(ctx.eventos), ctx.times, list(ctx.cores.values())))
    st.caption("Cada degrau é um chute; a altura do degrau é o xG (chance de gol) daquele chute.")

with aba_relacoes:
    viz.exibir(viz.dispersao_passes_xg(tab, ctx.times, list(ctx.cores.values())))
    opcoes = ["gols", "xg", "xa", "chutes", "passes", "precisao_passe", "passes_chave", "progressivos",
              "dribles_certos", "acoes_defensivas", "pressoes", "perdas", "indice"]
    escolhidas = st.multiselect("Estatísticas da matriz de correlação", opcoes, format_func=metricas.ROTULOS.get,
                                key=estado.preparar("corr_colunas", opcoes[:8] + ["indice"], opcoes),
                                on_change=estado.salvar, args=("corr_colunas",))
    if len(escolhidas) >= 2:
        viz.exibir(viz.heatmap_correlacao(tab[tab["minutos"] >= 15], escolhidas, metricas.ROTULOS))
        st.caption("Considera jogadores com 15 minutos ou mais. Azul: correlação positiva; vermelho: negativa.")

# Item 6.3: carga de várias partidas com barra de progresso
st.divider()
st.subheader("Contexto na competição")
st.markdown("O volume de chutes do time se converte em gols ao longo da competição?")
c1, c2 = st.columns([2, 3])
time = c1.radio("Time", ctx.times, horizontal=True, key=estado.preparar("contexto_time", ctx.times[0], ctx.times),
                on_change=estado.salvar, args=("contexto_time",))
partidas = dados.carregar_partidas(int(ctx.partida["competition_id"]), int(ctx.partida["season_id"]))
do_time = partidas[(partidas["home_team"] == time) | (partidas["away_team"] == time)]
chave_resumo = f"resumo_{ctx.partida['competition_id']}_{ctx.partida['season_id']}_{time}"
if c2.button(f"Carregar as {len(do_time)} partidas de {time}", icon=":material/download:"):
    eventos = dados.carregar_eventos_varias(do_time["match_id"].tolist())
    st.session_state[chave_resumo] = metricas.resumo_por_partida(eventos, time)

resumo = st.session_state.get(chave_resumo)
if resumo is not None:
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Partidas", len(resumo))
    m2.metric("Chutes por jogo", f"{resumo['chutes'].mean():.1f}")
    m3.metric("Gols por jogo", f"{resumo['gols'].mean():.2f}")
    m4.metric("Gols por chute", f"{100 * resumo['gols'].sum() / max(resumo['chutes'].sum(), 1):.1f}%",
              delta=f"{resumo['gols'].sum() - resumo['xg'].sum():+.1f} gols vs xG")
    viz.exibir(viz.regressao_chutes_gols(resumo, ctx.cores[time], time))
    st.dataframe(resumo.drop(columns="match_id"), hide_index=True)
