import pandas as pd
import streamlit as st

from futebol import estado, interface, metricas, visualizacoes as viz

ctx = estado.contexto()
st.title("Análise de jogador")

GRUPOS = {
    "Passes": ["Pass", "Ball Receipt*"],
    "Chutes": ["Shot"],
    "Conduções e dribles": ["Carry", "Dribble"],
    "Defesa": ["Interception", "Block", "Clearance", "Ball Recovery", "Duel", "Pressure"],
    "Outros": None,
}
CONHECIDOS = {t for tipos in GRUPOS.values() if tipos for t in tipos}
PIZZA = ["gols", "xg", "xa", "passes_chave", "passes_certos", "progressivos", "dribles_certos", "acoes_defensivas",
         "pressoes"]

# Item 6.1: seletor de jogador e botões de filtro por tipo de evento
nomes = interface.opcoes_jogadores(ctx)
c1, c2 = st.columns([2, 3])
jogador = c1.selectbox("Jogador", nomes, format_func=interface.rotulo_jogador(ctx),
                       key=estado.preparar("jogador", nomes[0], nomes), on_change=estado.salvar, args=("jogador",))
grupos = c2.pills("Tipos de evento", list(GRUPOS), selection_mode="multi",
                  key=estado.preparar("jogador_grupos", list(GRUPOS), list(GRUPOS)),
                  on_change=estado.salvar, args=("jogador_grupos",))

linha = ctx.jogadores.loc[jogador]
time = linha["time"]
cor = ctx.cores[time]
media = ctx.jogadores[ctx.jogadores["minutos"] >= 15].mean(numeric_only=True)

# Item 7: indicadores do jogador comparados com a média da partida
st.markdown(f"**{jogador}** · {time} · {int(linha['minutos'])} minutos em campo")
conversao = 100 * linha["gols"] / linha["chutes"] if linha["chutes"] else 0
indicadores = [
    ("Gols", "gols", 0, ""),
    ("Passes certos", "passes_certos", 0, ""),
    ("% de acerto no passe", "precisao_passe", 1, "%"),
    ("xG", "xg", 2, ""),
    ("xA", "xa", 2, ""),
    ("Ações progressivas", "progressivos", 0, ""),
    ("Ações defensivas", "acoes_defensivas", 0, ""),
]
fmt = interface.formatar_numero
with st.container(key="time_casa" if time == ctx.times[0] else "time_fora"):
    colunas = st.columns(4) + st.columns(4)
    for coluna, (rotulo, campo, casas, sufixo) in zip(colunas, indicadores):
        delta = linha[campo] - media[campo]
        coluna.metric(rotulo, f"{fmt(linha[campo], casas)}{sufixo}",
                      delta=f"{fmt(delta, casas)}{' p.p.' if sufixo else ''}" if round(delta, casas) else None,
                      help="Delta: diferença para a média dos jogadores com 15+ minutos na partida")
    colunas[-1].metric("Conversão de chutes", f"{fmt(conversao)}%",
                       help=f"{int(linha['gols'])} gols em {int(linha['chutes'])} chutes")

ev = ctx.eventos[ctx.eventos["player"] == jogador]
tipos = [t for g in grupos if GRUPOS[g] for t in GRUPOS[g]]
filtro = ev["type"].isin(tipos)
if "Outros" in grupos:
    filtro |= ~ev["type"].isin(CONHECIDOS)
ev = ev[filtro]

aba_pizza, aba_mapa, aba_tempo, aba_eventos = st.tabs(
    ["Perfil", "Mapa de ações", "Linha do tempo", "Eventos"], key="aba_jogador", on_change="rerun")

with aba_pizza:
    pc = metricas.percentis(ctx.jogadores, PIZZA)
    esquerda, direita = st.columns([3, 2])
    with esquerda, st.spinner("Desenhando o perfil..."):
        viz.exibir(viz.pizza_jogador([metricas.ROTULOS[c] for c in PIZZA], pc.loc[jogador].astype(int).tolist(),
                                     cor, jogador))
    with direita:
        perfil = pd.DataFrame({"Valor": linha[PIZZA], "Percentil": pc.loc[jogador]}).rename(index=metricas.ROTULOS)
        st.dataframe(perfil, column_config={"Percentil": st.column_config.ProgressColumn(
            min_value=0, max_value=100, format="%d")}, height=360)
        st.metric("Índice de decisão", f"{linha['indice']:.1f}",
                  delta=f"{int(ctx.jogadores['indice'].rank(ascending=False)[jogador])}º na partida",
                  delta_color="off", delta_arrow="off")

with aba_mapa:
    passes = ev[ev["type"] == "Pass"]
    esquerda, direita = st.columns(2)
    with esquerda, st.spinner("Desenhando..."):
        viz.exibir(viz.heatmap_acoes(ev, f"Ações de {jogador}", "densidade"))
    with direita, st.spinner("Desenhando..."):
        viz.exibir(viz.mapa_passes(passes, cor, f"Passes de {jogador}"))

with aba_tempo:
    if ev.empty:
        st.info("Nenhum evento para os filtros escolhidos.")
    else:
        viz.exibir(viz.linha_do_tempo(ev, cor))

with aba_eventos:
    tabela = interface.tabela_eventos(ev)
    st.dataframe(tabela, hide_index=True, column_config=interface.config_eventos(), height=420)
    # Item 6.2
    interface.botao_csv(tabela, f"eventos_{jogador.replace(' ', '_').lower()}.csv",
                        f"Baixar eventos de {jogador} (CSV)")
