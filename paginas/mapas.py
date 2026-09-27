import streamlit as st

from futebol import estado, interface, metricas, visualizacoes as viz

ctx = estado.contexto()
casa, fora = ctx.times
st.title("Mapas da partida")
st.caption(f"{casa} x {fora} · campos no padrão StatsBomb (120 x 80), sempre atacando para a direita")

# Item 8: formulário de filtros dos mapas
chaves = ["mapa_time", "mapa_jogador", "mapa_minutos", "mapa_max", "mapa_certos", "mapa_progressivos",
          "mapa_bola_parada", "mapa_calor", "mapa_rede_min"]
with st.form("form_mapas"):
    c1, c2, c3 = st.columns([2, 3, 3])
    time = c1.radio("Time", ctx.times, key=estado.preparar("mapa_time", casa, ctx.times))
    nomes = ["Todos"] + interface.opcoes_jogadores(ctx)
    jogador = c2.selectbox("Jogador (vale para passes e calor)", nomes,
                           key=estado.preparar("mapa_jogador", "Todos", nomes))
    minutos = c3.slider("Intervalo de minutos", 0, ctx.duracao, key=estado.preparar("mapa_minutos", (0, ctx.duracao)))
    c4, c5, c6, c7 = st.columns(4)
    maximo = c4.number_input("Máx. de passes no mapa", 10, 1500, step=10, key=estado.preparar("mapa_max", 250))
    rede_min = c5.number_input("Mín. de passes por dupla (rede)", 1, 15, key=estado.preparar("mapa_rede_min", 3))
    calor = c6.selectbox("Mapa de calor", ["grade", "densidade"], key=estado.preparar("mapa_calor", "grade"))
    with c7:
        so_certos = st.checkbox("Só passes certos", key=estado.preparar("mapa_certos", False))
        so_progressivos = st.checkbox("Só progressivos", key=estado.preparar("mapa_progressivos", False))
        sem_bola_parada = st.checkbox("Sem bola parada", key=estado.preparar("mapa_bola_parada", False))
    st.form_submit_button("Aplicar filtros", type="primary", on_click=estado.salvar, args=chaves)

if jogador != "Todos" and ctx.jogadores.loc[jogador, "time"] != time:
    st.info(f"{jogador} joga por {ctx.jogadores.loc[jogador, 'time']}; mostrando os mapas desse time.")
    time = ctx.jogadores.loc[jogador, "time"]

ev = interface.filtrar_minutos(metricas.em_jogo(ctx.eventos), minutos)
ev_time = ev[ev["team"] == time]
ev_foco = ev_time if jogador == "Todos" else ev_time[ev_time["player"] == jogador]
foco = time if jogador == "Todos" else jogador
cor = ctx.cores[time]

aba_passes, aba_chutes, aba_rede, aba_calor = st.tabs(
    ["Passes", "Chutes", "Rede de passes", "Calor e pressão"], key="aba_mapas", on_change="rerun")

# Item 5.1: mapa de passes
with aba_passes:
    passes = ev_foco[ev_foco["type"] == "Pass"]
    if sem_bola_parada:
        passes = passes[passes["pass_type"].isna() | passes["pass_type"].isin(["Recovery", "Interception"])]
    if so_certos:
        passes = passes[passes["passe_certo"]]
    if so_progressivos:
        passes = passes[passes["progressivo"]]
    total = len(passes)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Passes no filtro", total)
    m2.metric("Certos", int(passes["passe_certo"].sum()))
    m3.metric("Precisão", f"{interface.formatar_numero(100 * passes['passe_certo'].mean(), 1)}%" if total else "-")
    m4.metric("Progressivos", int(passes["progressivo"].sum()))
    passes = passes.head(int(maximo))
    if total > len(passes):
        st.caption(f"Mostrando os {len(passes)} primeiros de {total} passes (ajuste o máximo no formulário).")
    with st.spinner("Desenhando o mapa de passes..."):
        viz.exibir(viz.mapa_passes(passes, cor, f"Passes: {foco} ({minutos[0]}' a {minutos[1]}')"))
    st.caption("Progressivo: passe certo que aproxima a bola ao menos 25% do gol adversário e termina no campo de ataque.")

# Item 5.1: mapa de chutes, com destaque de um chute escolhido
with aba_chutes:
    chutes = ev[ev["type"] == "Shot"].reset_index(drop=True)
    if chutes.empty:
        st.info("Nenhum chute no intervalo selecionado.")
    else:
        rotulos = {
            i: f"{int(c['minute']) + 1}' {c['player']} ({c['team']}) · {c['resultado_chute']} · {c['xg']:.2f} xG"
            for i, c in chutes.iterrows()
        }
        opcoes = [None] + list(rotulos)
        mapa, detalhe = st.columns([3, 1])
        with detalhe:
            escolhido = st.selectbox("Destacar chute", opcoes, format_func=lambda i: "Nenhum" if i is None else rotulos[i],
                                     key=estado.preparar("chute_destaque", None, opcoes),
                                     on_change=estado.salvar, args=("chute_destaque",))
            if escolhido is not None:
                c = chutes.loc[escolhido]
                st.metric("xG do chute", f"{c['xg']:.2f}")
                st.markdown(
                    f"**{c['player']}** ({c['team']})  \n"
                    f"Minuto {int(c['minute']) + 1} · {c['resultado_chute']}  \n"
                    f"Tipo: {c['shot_type']} · parte do corpo: {c.get('shot_body_part', '-')}  \n"
                    f"Origem: {c['play_pattern']}"
                )
            for t in ctx.times:
                ct = chutes[chutes["team"] == t]
                st.metric(f"Conversão {t}", f"{100 * ct['gol'].mean():.0f}%" if len(ct) else "-",
                          delta=f"{ct['gol'].sum() - ct['xg'].sum():+.2f} gols vs xG", delta_color="normal")
        with mapa, st.spinner("Desenhando o mapa de chutes..."):
            destaque = chutes.loc[escolhido] if escolhido is not None else None
            viz.exibir(viz.mapa_chutes(chutes, ctx.times, list(ctx.cores.values()), destaque))
        st.caption("Pênaltis da disputa final não entram no mapa. Gols acima do xG indicam finalização acima do esperado.")

# Item 5.3: visualizações da galeria do mplsoccer
with aba_rede:
    with st.spinner("Montando a rede de passes..."):
        viz.exibir(viz.rede_passes(ev, time, cor, int(rede_min)))
    st.caption("Posição média de quem passa, até a primeira substituição do time dentro do intervalo escolhido.")

with aba_calor:
    esquerda, direita = st.columns(2)
    with esquerda, st.spinner("Calculando o mapa de calor..."):
        acoes = ev_foco[ev_foco["type"].isin(["Pass", "Carry", "Shot", "Dribble", "Ball Receipt*"])]
        viz.exibir(viz.heatmap_acoes(acoes, f"Onde {foco} teve a bola", calor))
    with direita, st.spinner("Calculando as zonas de pressão..."):
        viz.exibir(viz.mapa_pressoes(ev_time[ev_time["type"] == "Pressure"], f"Pressões de {time}"))
