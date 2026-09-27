import numpy as np
import pandas as pd
import pytest

from futebol import metricas
from futebol.dados import preparar_eventos


def evento(i, tipo, time, jogador, pid, minuto=10, periodo=1, **extra):
    base = {
        "id": f"e{i}", "index": i, "type": tipo, "team": time, "player": jogador, "player_id": pid,
        "possession_team": time, "duration": 1.0, "minute": minuto, "second": 0, "period": periodo,
        "location": [60.0, 40.0],
    }
    base.update(extra)
    return base


@pytest.fixture
def eventos():
    escalacao = {"lineup": [{"player": {"id": 1}}, {"player": {"id": 2}}]}
    escalacao_b = {"lineup": [{"player": {"id": 3}}]}
    brutos = [
        evento(0, "Starting XI", "A", None, np.nan, minuto=0, tactics=escalacao),
        evento(1, "Starting XI", "B", None, np.nan, minuto=0, tactics=escalacao_b),
        evento(2, "Pass", "A", "Ana", 1, location=[50.0, 40.0], pass_end_location=[100.0, 40.0],
               pass_shot_assist=True, pass_goal_assist=True, pass_assisted_shot_id="e3"),
        evento(3, "Shot", "A", "Bia", 2, location=[105.0, 40.0], shot_end_location=[120.0, 40.0],
               shot_outcome="Goal", shot_statsbomb_xg=0.4),
        evento(4, "Pass", "A", "Ana", 1, location=[30.0, 40.0], pass_end_location=[35.0, 40.0],
               pass_outcome="Incomplete"),
        evento(5, "Shot", "B", "Caio", 3, location=[100.0, 30.0], shot_outcome="Off T", shot_statsbomb_xg=0.1),
        evento(6, "Interception", "B", "Caio", 3),
        evento(7, "Substitution", "A", "Bia", 2, minuto=60, substitution_replacement="Duda",
               substitution_replacement_id=4),
        evento(8, "Shot", "B", "Caio", 3, minuto=90, location=[108.0, 40.0], shot_outcome="Goal",
               shot_statsbomb_xg=0.8),
        evento(9, "Shot", "A", "Ana", 1, minuto=121, periodo=5, location=[108.0, 40.0], shot_outcome="Goal",
               shot_statsbomb_xg=0.78),
    ]
    return preparar_eventos(pd.DataFrame(brutos))


def test_preparacao_extrai_coordenadas_e_passes(eventos):
    passe = eventos.loc[eventos["id"] == "e2"].iloc[0]
    assert (passe["x"], passe["x_fim"]) == (50.0, 100.0)
    assert passe["passe_certo"] and passe["progressivo"]
    assert not eventos.loc[eventos["id"] == "e4", "passe_certo"].iloc[0]


def test_estatisticas_time_ignoram_disputa_de_penaltis(eventos):
    a = metricas.estatisticas_time(eventos, "A")
    assert a["Gols"] == 1
    assert a["Chutes"] == 1
    assert a["Passes"] == 2
    assert a["Precisão de passe (%)"] == 50.0
    assert metricas.placar_penaltis(eventos) == {"A": 1}


def test_tabela_jogadores_calcula_xa_e_minutos(eventos):
    tab = metricas.tabela_jogadores(eventos)
    assert tab.loc["Ana", "assistencias"] == 1
    assert tab.loc["Ana", "xa"] == pytest.approx(0.4)
    assert tab.loc["Ana", "gols"] == 0
    assert tab.loc["Bia", "minutos"] == 60
    assert tab.loc["Caio", "acoes_defensivas"] == 1


def test_indice_normaliza_pelo_melhor_da_partida(eventos):
    tab = metricas.tabela_jogadores(eventos)
    indice = metricas.indice_decisao(tab, {"gols": 1.0})
    assert indice.max() == 100
    assert indice["Ana"] == 0
    familias = metricas.contribuicoes_por_familia(tab)
    assert np.allclose(familias.sum(axis=1).round(1), metricas.indice_decisao(tab))


def test_indice_sem_pesos_vale_zero(eventos):
    tab = metricas.tabela_jogadores(eventos)
    assert (metricas.indice_decisao(tab, {"gols": 0}) == 0).all()
