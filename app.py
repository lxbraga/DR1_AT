import streamlit as st

from futebol import estado, interface

st.set_page_config(page_title="Quem decidiu a partida?", page_icon="⚽", layout="wide")
interface.aplicar_estilo()

paginas = st.navigation([
    st.Page("paginas/visao_geral.py", title="Visão geral", icon=":material/scoreboard:", default=True),
    st.Page("paginas/mapas.py", title="Mapas da partida", icon=":material/stadium:"),
    st.Page("paginas/jogador.py", title="Jogador", icon=":material/person:"),
    st.Page("paginas/comparacao.py", title="Comparação", icon=":material/compare_arrows:"),
    st.Page("paginas/analises.py", title="Quem decidiu?", icon=":material/insights:"),
])

# Item 3: seletores globais na barra lateral
with st.sidebar:
    st.header("⚽ Seleção")
    estado.seletores_partida()
    st.divider()
    st.caption("Dados: [StatsBomb Open Data](https://github.com/statsbomb/open-data)")
    # Item 9.2
    with st.expander("Estado da sessão"):
        st.json(estado.resumo_do_estado(), expanded=False)

paginas.run()
