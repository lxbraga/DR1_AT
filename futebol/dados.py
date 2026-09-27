import warnings

import numpy as np
import pandas as pd
import streamlit as st
from statsbombpy import sb

warnings.filterwarnings("ignore", module="statsbombpy")

TIPOS_DEFENSIVOS = {"Interception", "Block", "Clearance", "Ball Recovery"}
COLUNAS_ESPERADAS = [
    "pass_outcome", "pass_type", "pass_goal_assist", "pass_shot_assist", "pass_assisted_shot_id",
    "pass_recipient", "pass_recipient_id", "pass_end_location", "carry_end_location", "shot_end_location",
    "shot_outcome", "shot_statsbomb_xg", "shot_type", "duel_type", "duel_outcome", "dribble_outcome",
    "interception_outcome",
    "foul_committed_card", "bad_behaviour_card", "substitution_replacement", "substitution_replacement_id",
    "tactics", "under_pressure",
]
TRADUCAO_RESULTADOS = {
    "Incomplete": "Incompleto", "Out": "Saiu", "Pass Offside": "Impedimento", "Unknown": "Desconhecido",
    "Injury Clearance": "Bola fora (lesão)", "Won": "Ganhou", "Lost": "Perdeu", "Lost In Play": "Perdeu",
    "Lost Out": "Perdeu (saiu)", "Success": "Sucesso", "Success In Play": "Sucesso", "Success Out": "Sucesso (saiu)",
    "Complete": "Certo", "Incomplete Dribble": "Errado", "Tackle": "Desarme", "Aerial Lost": "Aéreo perdido",
}
GOL_ADVERSARIO = (120, 40)
TRADUCAO_TIPOS = {
    "Pass": "Passe", "Ball Receipt*": "Recepção", "Carry": "Condução", "Pressure": "Pressão",
    "Ball Recovery": "Recuperação", "Duel": "Duelo", "Dribble": "Drible", "Block": "Bloqueio",
    "Foul Committed": "Falta cometida", "Clearance": "Corte", "Foul Won": "Falta sofrida",
    "Goal Keeper": "Goleiro", "Shot": "Chute", "Miscontrol": "Domínio errado", "Dispossessed": "Desarmado",
    "Dribbled Past": "Driblado", "Interception": "Interceptação", "Substitution": "Substituição",
    "Half Start": "Início de tempo", "Half End": "Fim de tempo", "Injury Stoppage": "Parada por lesão",
    "50/50": "Dividida", "Tactical Shift": "Mudança tática", "Starting XI": "Escalação",
    "Bad Behaviour": "Conduta", "Offside": "Impedimento", "Shield": "Proteção", "Player On": "Jogador volta",
    "Player Off": "Jogador sai", "Own Goal For": "Gol contra (a favor)", "Own Goal Against": "Gol contra",
    "Error": "Erro", "Referee Ball-Drop": "Bola ao chão",
}
TRADUCAO_RESULTADO_CHUTE = {
    "Goal": "Gol", "Saved": "Defendido", "Saved To Post": "Defendido (trave)", "Saved Off Target": "Defendido (fora)",
    "Off T": "Fora", "Post": "Trave", "Blocked": "Bloqueado", "Wayward": "Muito fora",
}


@st.cache_data(show_spinner=False, ttl="1d")
def carregar_competicoes():
    df = sb.competitions()
    return df.sort_values(["competition_name", "season_name"], ascending=[True, False]).reset_index(drop=True)


@st.cache_data(show_spinner=False, ttl="1d")
def carregar_partidas(competition_id, season_id):
    df = sb.matches(competition_id=competition_id, season_id=season_id)
    df = df.sort_values(["match_date", "kick_off"]).reset_index(drop=True)
    df["rotulo"] = (
        df["match_date"] + " · " + df["home_team"] + " " + df["home_score"].astype(str) + " x "
        + df["away_score"].astype(str) + " " + df["away_team"] + " (" + df["competition_stage"] + ")"
    )
    return df


@st.cache_data(show_spinner=False)
def carregar_escalacoes(match_id):
    partes = []
    for time, df in sb.lineups(match_id=match_id).items():
        df = df.copy()
        df["time"] = time
        df["nome"] = df["player_nickname"].fillna(df["player_name"])
        df["posicao"] = df["positions"].map(lambda p: p[0]["position"] if p else None)
        df["jogou"] = df["positions"].map(bool)
        partes.append(df[["player_id", "player_name", "nome", "jersey_number", "time", "posicao", "jogou"]])
    return pd.concat(partes, ignore_index=True)


@st.cache_data(show_spinner=False)
def carregar_eventos(match_id):
    eventos = sb.events(match_id=match_id)
    escalacoes = carregar_escalacoes(match_id)
    return preparar_eventos(eventos, dict(zip(escalacoes["player_id"], escalacoes["nome"])))


def carregar_eventos_varias(match_ids):
    barra = st.progress(0.0, text="Preparando...")
    partes = []
    for i, match_id in enumerate(match_ids, start=1):
        partes.append(carregar_eventos(match_id))
        barra.progress(i / len(match_ids), text=f"Carregando partida {i} de {len(match_ids)}")
    barra.empty()
    return pd.concat(partes, ignore_index=True)


def _traduzir(serie, mapa):
    return serie.map(lambda v: mapa.get(v, v))


def _coordenada(serie, i):
    return serie.map(lambda v: v[i] if isinstance(v, (list, tuple)) and len(v) > i else np.nan).astype(float)


def preparar_eventos(df, nomes=None):
    df = df.copy()
    for coluna in COLUNAS_ESPERADAS:
        if coluna not in df:
            df[coluna] = np.nan
    if "index" in df:
        df = df.sort_values("index")
    df = df.reset_index(drop=True)

    if nomes:
        df["player"] = df["player_id"].map(nomes).fillna(df["player"])
        df["pass_recipient"] = df["pass_recipient_id"].map(nomes).fillna(df["pass_recipient"])
        df["substitution_replacement"] = (
            df["substitution_replacement_id"].map(nomes).fillna(df["substitution_replacement"])
        )

    fim = df["pass_end_location"].combine_first(df["carry_end_location"]).combine_first(df["shot_end_location"])
    df["x"], df["y"] = _coordenada(df["location"], 0), _coordenada(df["location"], 1)
    df["x_fim"], df["y_fim"] = _coordenada(fim, 0), _coordenada(fim, 1)
    df["tempo"] = df["minute"] + df["second"] / 60
    df["tipo"] = _traduzir(df["type"], TRADUCAO_TIPOS)

    df["passe_certo"] = df["type"].eq("Pass") & df["pass_outcome"].isna()
    dist_ini = np.hypot(GOL_ADVERSARIO[0] - df["x"], GOL_ADVERSARIO[1] - df["y"])
    dist_fim = np.hypot(GOL_ADVERSARIO[0] - df["x_fim"], GOL_ADVERSARIO[1] - df["y_fim"])
    df["progressivo"] = (
        (df["passe_certo"] | df["type"].eq("Carry"))
        & ~df["pass_type"].isin(["Corner", "Throw-in"])
        & (dist_fim <= 0.75 * dist_ini)
        & (df["x_fim"] >= 60)
    )
    df["acao_defensiva"] = df["type"].isin(TIPOS_DEFENSIVOS) | (
        df["type"].eq("Duel") & df["duel_type"].eq("Tackle")
    )
    df["gol"] = df["type"].eq("Shot") & df["shot_outcome"].eq("Goal")
    df["xg"] = df["shot_statsbomb_xg"].fillna(0.0)
    df["resultado_chute"] = _traduzir(df["shot_outcome"], TRADUCAO_RESULTADO_CHUTE)
    outros = df["duel_outcome"].combine_first(df["dribble_outcome"]).combine_first(df["interception_outcome"])
    df["resultado"] = np.select(
        [df["passe_certo"], df["type"].eq("Pass"), df["type"].eq("Shot")],
        ["Certo", _traduzir(df["pass_outcome"], TRADUCAO_RESULTADOS), df["resultado_chute"]],
        default=_traduzir(outros, TRADUCAO_RESULTADOS),
    )
    df["disputa_penaltis"] = df["period"].eq(5)
    return df
