import pandas as pd

PESOS_PADRAO = {
    "gols": 3.0, "assistencias": 2.0, "xg": 2.0, "xa": 2.0,
    "passes_chave": 1.0, "progressivos": 0.5, "acoes_defensivas": 0.5,
}
ROTULOS = {
    "minutos": "Minutos", "gols": "Gols", "assistencias": "Assistências", "chutes": "Chutes",
    "chutes_no_alvo": "Chutes no alvo", "xg": "xG", "xa": "xA", "passes": "Passes",
    "passes_certos": "Passes certos", "precisao_passe": "% passes certos", "passes_chave": "Passes-chave",
    "progressivos": "Ações progressivas", "conducoes": "Conduções", "dribles_certos": "Dribles certos",
    "acoes_defensivas": "Ações defensivas", "pressoes": "Pressões", "perdas": "Perdas de posse",
    "indice": "Índice de decisão",
}
FAMILIAS = {
    "gols": "Finalização", "xg": "Finalização",
    "assistencias": "Criação", "xa": "Criação", "passes_chave": "Criação",
    "progressivos": "Progressão", "acoes_defensivas": "Defesa",
}
NO_ALVO = {"Goal", "Saved", "Saved To Post"}
CARTOES_EXPULSAO = {"Red Card", "Second Yellow"}


def em_jogo(ev):
    return ev[~ev["disputa_penaltis"]]


def _razao(a, b):
    return a / b if b else 0.0


def estatisticas_time(ev, time):
    e = em_jogo(ev)
    t = e[e["team"] == time]
    chutes = t[t["type"] == "Shot"]
    passes = t[t["type"] == "Pass"]
    gols = int(chutes["gol"].sum() + t["type"].eq("Own Goal For").sum())
    duracao = e.groupby("possession_team")["duration"].sum()
    return {
        "Gols": gols,
        "Chutes": len(chutes),
        "Chutes no alvo": int(chutes["shot_outcome"].isin(NO_ALVO).sum()),
        "xG": round(float(chutes["xg"].sum()), 2),
        "Conversão (%)": round(100 * _razao(gols, len(chutes)), 1),
        "Passes": len(passes),
        "Passes certos": int(passes["passe_certo"].sum()),
        "Precisão de passe (%)": round(100 * _razao(passes["passe_certo"].sum(), len(passes)), 1),
        "Ações progressivas": int(t["progressivo"].sum()),
        "Posse (%)": round(100 * _razao(duracao.get(time, 0), duracao.sum()), 1),
        "Ações defensivas": int(t["acao_defensiva"].sum()),
        "Pressões": int(t["type"].eq("Pressure").sum()),
        "Faltas": int(t["type"].eq("Foul Committed").sum()),
        "Escanteios": int(passes["pass_type"].eq("Corner").sum()),
        "Impedimentos": int(t["type"].eq("Offside").sum() + passes["pass_outcome"].eq("Pass Offside").sum()),
    }


def estatisticas_partida(ev, times):
    return pd.DataFrame({time: estatisticas_time(ev, time) for time in times})


def placar_penaltis(ev):
    chutes = ev[ev["disputa_penaltis"] & ev["type"].eq("Shot")]
    return chutes.groupby("team")["gol"].sum().astype(int).to_dict() if len(chutes) else {}


def minutos_jogados(ev):
    fim = em_jogo(ev)["tempo"].max()
    entrada, saida = {}, {}
    for tatica in ev.loc[ev["type"] == "Starting XI", "tactics"]:
        for item in tatica["lineup"]:
            entrada[item["player"]["id"]] = 0.0
    for _, sub in ev[ev["type"] == "Substitution"].iterrows():
        saida[sub["player_id"]] = sub["tempo"]
        entrada[sub["substitution_replacement_id"]] = sub["tempo"]
    expulsos = ev[ev["foul_committed_card"].isin(CARTOES_EXPULSAO) | ev["bad_behaviour_card"].isin(CARTOES_EXPULSAO)]
    for _, cartao in expulsos.iterrows():
        saida[cartao["player_id"]] = cartao["tempo"]
    return pd.Series({pid: saida.get(pid, fim) - ini for pid, ini in entrada.items()}, dtype=float)


def tabela_jogadores(ev):
    e = em_jogo(ev)
    e = e[e["player_id"].notna()]
    xg_por_chute = e.loc[e["type"] == "Shot"].set_index("id")["xg"]
    chute = e["type"].eq("Shot")
    passe = e["type"].eq("Pass")
    assistencia = passe & e["pass_goal_assist"].eq(True)
    indicadores = pd.DataFrame({
        "player_id": e["player_id"],
        "jogador": e["player"],
        "time": e["team"],
        "gols": e["gol"],
        "assistencias": assistencia,
        "chutes": chute,
        "chutes_no_alvo": chute & e["shot_outcome"].isin(NO_ALVO),
        "xg": e["xg"],
        "xa": e["pass_assisted_shot_id"].map(xg_por_chute).fillna(0.0),
        "passes": passe,
        "passes_certos": e["passe_certo"],
        "passes_chave": passe & (e["pass_shot_assist"].eq(True) | assistencia),
        "progressivos": e["progressivo"],
        "conducoes": e["type"].eq("Carry"),
        "dribles_certos": e["type"].eq("Dribble") & e["dribble_outcome"].eq("Complete"),
        "acoes_defensivas": e["acao_defensiva"],
        "pressoes": e["type"].eq("Pressure"),
        "perdas": e["type"].isin(["Dispossessed", "Miscontrol"]),
    })
    tab = indicadores.groupby(["player_id", "jogador", "time"]).sum().reset_index()
    tab["player_id"] = tab["player_id"].astype(int)
    tab.insert(3, "minutos", tab["player_id"].map(minutos_jogados(ev)).fillna(0).round(0))
    tab["precisao_passe"] = (100 * tab["passes_certos"] / tab["passes"].where(tab["passes"] > 0)).fillna(0).round(1)
    tab[["xg", "xa"]] = tab[["xg", "xa"]].round(2)
    return tab.set_index("jogador")


def contribuicoes_indice(tab, pesos=None):
    pesos = {k: v for k, v in (pesos or PESOS_PADRAO).items() if v}
    if not pesos:
        return pd.DataFrame(index=tab.index)
    colunas = list(pesos)
    normalizado = tab[colunas] / tab[colunas].max().replace(0, 1)
    return 100 * normalizado.mul(pd.Series(pesos)) / sum(pesos.values())


def contribuicoes_por_familia(tab, pesos=None):
    contrib = contribuicoes_indice(tab, pesos)
    familias = [f for f in dict.fromkeys(FAMILIAS.values())]
    agrupado = contrib.T.groupby(FAMILIAS).sum().T
    return agrupado.reindex(columns=[f for f in familias if f in agrupado.columns])


def indice_decisao(tab, pesos=None):
    return contribuicoes_indice(tab, pesos).sum(axis=1).round(1)


def por_90(tab, colunas):
    minutos = tab["minutos"].where(tab["minutos"] > 0)
    return tab[colunas].div(minutos, axis=0).mul(90).fillna(0).round(2)


def percentis(tab, colunas):
    return (tab[colunas].rank(pct=True) * 100).round(0)


def serie_xg_acumulado(ev):
    chutes = em_jogo(ev)
    chutes = chutes[chutes["type"] == "Shot"].sort_values("tempo")
    chutes = chutes.assign(xg_acumulado=chutes.groupby("team")["xg"].cumsum())
    return chutes[["tempo", "team", "player", "xg", "xg_acumulado", "gol"]]


def resumo_por_partida(ev, time):
    linhas = []
    for match_id, e in ev.groupby("match_id"):
        adversario = next((t for t in e["team"].unique() if t != time), "")
        est, est_adv = estatisticas_time(e, time), estatisticas_time(e, adversario)
        linhas.append({
            "match_id": match_id, "adversario": adversario,
            "chutes": est["Chutes"], "xg": est["xG"], "gols": est["Gols"],
            "gols_sofridos": est_adv["Gols"], "posse": est["Posse (%)"], "passes": est["Passes"],
        })
    return pd.DataFrame(linhas)
