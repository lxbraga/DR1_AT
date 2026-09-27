from dataclasses import dataclass

import pandas as pd
import streamlit as st

from futebol import dados, metricas
from futebol.visualizacoes import CORES_TIMES

COMPETICAO_PADRAO = "FIFA World Cup"
TEMPORADA_PADRAO = "2022"
PARTIDA_PADRAO = 3869685
DEPENDENTES_DA_PARTIDA = [
    "jogador", "jogador_a", "jogador_b", "mapa_jogador", "mapa_minutos", "ev_jogador", "ev_tipos", "ev_time",
    "chute_destaque",
]


@dataclass
class Contexto:
    competicao: str
    temporada: str
    partida: pd.Series
    eventos: pd.DataFrame
    escalacoes: pd.DataFrame
    jogadores: pd.DataFrame

    @property
    def times(self):
        return [self.partida["home_team"], self.partida["away_team"]]

    @property
    def cores(self):
        return dict(zip(self.times, CORES_TIMES))

    @property
    def duracao(self):
        return int(metricas.em_jogo(self.eventos)["tempo"].max()) + 1


def preparar(chave, padrao, opcoes=None):
    atual = st.session_state.get(chave, padrao)
    if opcoes is not None:
        opcoes = list(opcoes)
        if isinstance(atual, list):
            atual = [a for a in atual if a in opcoes]
        elif atual not in opcoes:
            atual = padrao if padrao in opcoes else opcoes[0]
    st.session_state[chave] = atual
    st.session_state[f"_w_{chave}"] = atual
    return f"_w_{chave}"


def salvar(*chaves):
    for chave in chaves:
        st.session_state[chave] = st.session_state[f"_w_{chave}"]


def _limpar_dependentes():
    for chave in DEPENDENTES_DA_PARTIDA:
        st.session_state.pop(chave, None)


def trocar_partida():
    salvar("partida")
    _limpar_dependentes()


def seletores_partida():
    competicoes = dados.carregar_competicoes()
    nomes = competicoes["competition_name"].unique().tolist()
    competicao = st.selectbox("Competição", nomes, key=preparar("competicao", COMPETICAO_PADRAO, nomes),
                              on_change=salvar, args=("competicao",))

    temporadas = competicoes.loc[competicoes["competition_name"] == competicao]
    rotulos = temporadas["season_name"].tolist()
    temporada = st.selectbox("Temporada", rotulos, key=preparar("temporada", TEMPORADA_PADRAO, rotulos),
                             on_change=salvar, args=("temporada",))
    linha = temporadas.loc[temporadas["season_name"] == temporada].iloc[0]

    with st.spinner("Buscando partidas..."):
        partidas = dados.carregar_partidas(int(linha["competition_id"]), int(linha["season_id"]))
    ids = [int(i) for i in partidas["match_id"]]
    rotulo_por_id = dict(zip(ids, partidas["rotulo"]))
    padrao = PARTIDA_PADRAO if PARTIDA_PADRAO in ids else ids[-1]
    anterior = st.session_state.get("partida")
    chave = preparar("partida", padrao, ids)
    if st.session_state["partida"] != anterior:
        _limpar_dependentes()
    st.selectbox("Partida", ids, format_func=rotulo_por_id.get, key=chave, on_change=trocar_partida)
    st.caption(f"{len(ids)} partidas disponíveis nesta temporada")


@st.cache_data(show_spinner=False)
def _tabela_jogadores(match_id):
    return metricas.tabela_jogadores(dados.carregar_eventos(match_id))


def contexto():
    competicoes = dados.carregar_competicoes()
    linha = competicoes[(competicoes["competition_name"] == st.session_state["competicao"])
                        & (competicoes["season_name"] == st.session_state["temporada"])].iloc[0]
    partidas = dados.carregar_partidas(int(linha["competition_id"]), int(linha["season_id"]))
    partida = partidas.loc[partidas["match_id"] == st.session_state["partida"]].iloc[0]
    with st.spinner("Carregando eventos da partida..."):
        eventos = dados.carregar_eventos(int(partida["match_id"]))
        escalacoes = dados.carregar_escalacoes(int(partida["match_id"]))
        jogadores = _tabela_jogadores(int(partida["match_id"])).copy()
    jogadores["indice"] = metricas.indice_decisao(jogadores, st.session_state.get("pesos"))
    return Contexto(linha["competition_name"], linha["season_name"], partida, eventos, escalacoes, jogadores)


def resumo_do_estado():
    return {k: v for k, v in st.session_state.items() if not str(k).startswith("_w_")}
