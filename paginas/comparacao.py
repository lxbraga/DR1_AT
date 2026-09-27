import streamlit as st

from futebol import estado, interface, metricas, visualizacoes as viz

ctx = estado.contexto()
st.title("Comparação entre jogadores")

METRICAS = ["gols", "xg", "xa", "chutes", "passes_chave", "passes_certos", "precisao_passe", "progressivos",
            "dribles_certos", "acoes_defensivas", "pressoes", "perdas"]
PADRAO = ["gols", "xg", "xa", "passes_chave", "progressivos", "acoes_defensivas"]

busca = st.text_input("Filtrar jogadores pelo nome", key=estado.preparar("busca_jogador", ""),
                      on_change=estado.salvar, args=("busca_jogador",), placeholder="ex.: Messi")
todos = interface.opcoes_jogadores(ctx)
nomes = [n for n in todos if busca.lower() in n.lower()]
if len(nomes) < 2:
    if busca:
        st.caption("A busca precisa encontrar ao menos dois jogadores; mostrando todos.")
    nomes = todos

padrao_a = next((n for n in nomes if ctx.jogadores.loc[n, "time"] == ctx.times[0]), nomes[0])
padrao_b = next((n for n in nomes if ctx.jogadores.loc[n, "time"] == ctx.times[1]), nomes[-1])

# Item 8: formulário de comparação entre dois jogadores
chaves = ["jogador_a", "jogador_b", "comp_metricas", "comp_escala", "comp_tabela"]
with st.form("form_comparacao"):
    c1, c2 = st.columns(2)
    formatar = interface.rotulo_jogador(ctx)
    a = c1.selectbox("Jogador A", nomes, format_func=formatar, key=estado.preparar("jogador_a", padrao_a, nomes))
    b = c2.selectbox("Jogador B", nomes, format_func=formatar, key=estado.preparar("jogador_b", padrao_b, nomes))
    escolhidas = st.multiselect("Estatísticas do radar (3 a 10)", METRICAS, format_func=metricas.ROTULOS.get,
                                max_selections=10, key=estado.preparar("comp_metricas", PADRAO, METRICAS))
    c3, c4 = st.columns(2)
    escala = c3.radio("Escala", ["Totais", "Por 90 minutos"], horizontal=True,
                      key=estado.preparar("comp_escala", "Totais"))
    mostrar_tabela = c4.checkbox("Mostrar tabela lado a lado", key=estado.preparar("comp_tabela", True))
    st.form_submit_button("Comparar", type="primary", on_click=estado.salvar, args=chaves)

if a == b:
    st.warning("Escolha dois jogadores diferentes.")
    st.stop()
if len(escolhidas) < 3:
    st.warning("Escolha pelo menos 3 estatísticas para o radar.")
    st.stop()

tab = ctx.jogadores.copy()
if escala == "Por 90 minutos":
    base = tab[tab["minutos"] >= 15]
    tab = metricas.por_90(base, [m for m in escolhidas if m != "precisao_passe"]).join(
        base[["time", "minutos", "precisao_passe"]])
    if a not in tab.index or b not in tab.index:
        st.warning("Por 90 minutos só considera jogadores com 15 minutos ou mais em campo.")
        st.stop()

cores = [ctx.cores[ctx.jogadores.loc[a, "time"]], ctx.cores[ctx.jogadores.loc[b, "time"]]]
if cores[0] == cores[1]:
    cores[1] = viz.CATEGORICAS[2]

esquerda, direita = st.columns([3, 2])
with esquerda, st.spinner("Desenhando o radar..."):
    viz.exibir(viz.radar_comparacao(
        [metricas.ROTULOS[m] for m in escolhidas], tab.loc[a, escolhidas].tolist(), tab.loc[b, escolhidas].tolist(),
        tab[escolhidas].max().tolist(), [a, b], cores,
    ))
    st.caption("A borda do radar é o maior valor entre todos os jogadores da partida em cada estatística.")

with direita:
    vitorias_a = int((tab.loc[a, escolhidas] > tab.loc[b, escolhidas]).sum())
    vitorias_b = int((tab.loc[b, escolhidas] > tab.loc[a, escolhidas]).sum())
    m1, m2 = st.columns(2)
    m1.metric(a, f"{vitorias_a} de {len(escolhidas)}", help="Estatísticas em que o jogador foi superior")
    m2.metric(b, f"{vitorias_b} de {len(escolhidas)}", help="Estatísticas em que o jogador foi superior")
    ia, ib = ctx.jogadores.loc[a, "indice"], ctx.jogadores.loc[b, "indice"]
    st.metric(f"Índice de decisão de {a}", f"{ia:.1f}", delta=f"{ia - ib:+.1f} vs {b}")
    if mostrar_tabela:
        lado_a_lado = tab.loc[[a, b], escolhidas].T.rename(index=metricas.ROTULOS)
        st.dataframe(lado_a_lado.style.highlight_max(axis=1, color="#cde2fb").format("{:.2f}"))

with st.spinner("Desenhando as barras..."):
    viz.exibir(viz.barras_comparacao(tab, [a, b], escolhidas, metricas.ROTULOS, cores))
