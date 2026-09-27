import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st
from matplotlib import patheffects
from matplotlib.colors import LinearSegmentedColormap, to_rgba
from matplotlib.lines import Line2D
from mplsoccer import Pitch, PyPizza, Radar, VerticalPitch

SUPERFICIE = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_2 = "#52514e"
APAGADO = "#898781"
GRADE = "#e1e0d9"
LINHAS_CAMPO = "#c3c2b7"
CORES_TIMES = ["#2a78d6", "#eb6834"]
CATEGORICAS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
COR_GOL = "#0ca30c"
AZUIS = LinearSegmentedColormap.from_list("azuis", ["#f0efec", "#9ec5f4", "#3987e5", "#1c5cab", "#0d366b"])
DIVERGENTE = LinearSegmentedColormap.from_list("divergente", ["#e34948", "#f0efec", "#2a78d6"])

CONTORNO = [patheffects.withStroke(linewidth=3, foreground=SUPERFICIE)]
PARTICULAS = {"di", "de", "da", "do", "dos", "das", "del", "van", "von", "le", "la", "mac"}

plt.rcParams.update({
    "figure.facecolor": SUPERFICIE, "axes.facecolor": SUPERFICIE, "savefig.facecolor": SUPERFICIE,
    "text.color": TINTA, "axes.labelcolor": TINTA_2, "xtick.color": APAGADO, "ytick.color": APAGADO,
    "axes.edgecolor": LINHAS_CAMPO, "grid.color": GRADE, "axes.spines.top": False, "axes.spines.right": False,
    "font.family": "sans-serif", "font.size": 10, "axes.titleweight": "bold", "legend.frameon": False,
})


def exibir(fig):
    st.pyplot(fig)
    plt.close(fig)


def _campo(vertical=False, **kwargs):
    classe = VerticalPitch if vertical else Pitch
    opcoes = dict(pitch_type="statsbomb", pitch_color=SUPERFICIE, line_color=LINHAS_CAMPO, linewidth=1.2)
    opcoes.update(kwargs)
    return classe(**opcoes)


def _legenda(ax, itens, **kwargs):
    alcas = [
        Line2D([], [], color=cor, marker=marcador, linestyle=linha, markersize=8, linewidth=2, label=rotulo,
               markerfacecolor=preenchimento or cor)
        for rotulo, cor, marcador, linha, preenchimento in itens
    ]
    opcoes = dict(loc="upper center", bbox_to_anchor=(0.5, 0.02), ncol=len(itens), fontsize=9, handlelength=1.6)
    opcoes.update(kwargs)
    ax.legend(handles=alcas, **opcoes)


def _sobrenome(nome):
    partes = str(nome).split()
    if len(partes) > 2 and partes[-2].lower() in PARTICULAS:
        return " ".join(partes[-2:])
    return partes[-1]


def _minuto(evento):
    return f"{int(evento['tempo']) + 1}'"


def mapa_passes(passes, cor, titulo):
    pitch = _campo()
    fig, ax = pitch.draw(figsize=(10, 7))
    errados = passes[~passes["passe_certo"]]
    certos = passes[passes["passe_certo"] & ~passes["progressivo"]]
    progressivos = passes[passes["passe_certo"] & passes["progressivo"]]
    grupos = [
        (errados, to_rgba(APAGADO, 0.6), f"Errados ({len(errados)})"),
        (certos, to_rgba(cor, 0.3), f"Certos ({len(certos)})"),
        (progressivos, to_rgba(cor, 1.0), f"Certos e progressivos ({len(progressivos)})"),
    ]
    for df, c, _ in grupos:
        pitch.arrows(df["x"], df["y"], df["x_fim"], df["y_fim"], ax=ax, color=c,
                     width=1.6, headwidth=4, headlength=4)
    _legenda(ax, [(r, c, None, "-", None) for _, c, r in grupos])
    ax.set_title(titulo, fontsize=13)
    ax.annotate("Ataque →", xy=(0.99, 1.0), xycoords="axes fraction", ha="right", va="bottom",
                fontsize=9, color=TINTA_2)
    return fig


def mapa_chutes(chutes, times, cores, destaque=None):
    pitch = _campo()
    fig, ax = pitch.draw(figsize=(11, 7.5))
    for i, (time, cor) in enumerate(zip(times, cores)):
        c = chutes[chutes["team"] == time]
        x = c["x"] if i == 0 else 120 - c["x"]
        y = c["y"] if i == 0 else 80 - c["y"]
        tamanhos = 80 + c["xg"] * 1400
        gols = c["gol"].to_numpy()
        no_alvo = c["shot_outcome"].isin({"Saved", "Saved To Post"}).to_numpy()
        fora = ~(gols | no_alvo)
        pitch.scatter(x[gols], y[gols], s=tamanhos[gols], marker="football", ax=ax, zorder=4)
        pitch.scatter(x[no_alvo], y[no_alvo], s=tamanhos[no_alvo], color=cor, edgecolors=SUPERFICIE,
                      linewidth=1.5, alpha=0.9, ax=ax, zorder=3)
        pitch.scatter(x[fora], y[fora], s=tamanhos[fora], facecolors="none", edgecolors=cor,
                      linewidth=2, ax=ax, zorder=3)
        gols_df = c[c["gol"]].assign(gx=x[gols], gy=y[gols])
        for (_, _, jogador), grupo in gols_df.groupby([gols_df["gx"].round(), gols_df["gy"].round(), "player"]):
            minutos = ", ".join(_minuto(g) for _, g in grupo.iterrows())
            pitch.annotate(f"{_sobrenome(jogador)} {minutos}", (grupo["gx"].iloc[0], grupo["gy"].iloc[0] - 3.5),
                           ax=ax, ha="center", fontsize=8, color=TINTA, zorder=5, path_effects=CONTORNO)
        ax.text(60 + (30 if i == 0 else -30), -3, f"{time}: {int(c['gol'].sum())} gols · {c['xg'].sum():.2f} xG",
                ha="center", fontsize=11, color=cor, fontweight="bold")
    if destaque is not None:
        i = times.index(destaque["team"])
        dx, dy = (destaque["x"], destaque["y"]) if i == 0 else (120 - destaque["x"], 80 - destaque["y"])
        pitch.scatter(dx, dy, s=900, facecolors="none", edgecolors=TINTA, linewidth=2.5, linestyle="--",
                      ax=ax, zorder=6)
    _legenda(ax, [
        ("Gol", TINTA, "o", "", "white"),
        ("No alvo", APAGADO, "o", "", None),
        ("Fora ou bloqueado", APAGADO, "o", "", "none"),
    ])
    ax.annotate("Tamanho do marcador = xG do chute", xy=(0.5, -0.07), xycoords="axes fraction", ha="center",
                va="top", fontsize=9, color=TINTA_2)
    return fig


def rede_passes(ev, time, cor, min_passes=3):
    e = ev[(ev["team"] == time) & ~ev["disputa_penaltis"]]
    subs = e.loc[e["type"] == "Substitution", "tempo"]
    limite = subs.min() if len(subs) else e["tempo"].max()
    passes = e[(e["type"] == "Pass") & e["passe_certo"] & (e["tempo"] < limite) & e["pass_recipient"].notna()]
    posicoes = passes.groupby("player").agg(x=("x", "mean"), y=("y", "mean"), n=("id", "size"))
    pares = passes.groupby(["player", "pass_recipient"]).size().reset_index(name="qtd")
    pares = pares[(pares["qtd"] >= min_passes) & pares["pass_recipient"].isin(posicoes.index)]
    pares = pares.join(posicoes[["x", "y"]], on="player").join(
        posicoes[["x", "y"]], on="pass_recipient", rsuffix="_fim")

    pitch = _campo()
    fig, ax = pitch.draw(figsize=(10, 7))
    if len(pares):
        larguras = 1 + 8 * pares["qtd"] / pares["qtd"].max()
        pitch.lines(pares["x"], pares["y"], pares["x_fim"], pares["y_fim"], lw=larguras, color=cor,
                    alpha=0.35, zorder=1, ax=ax)
    pitch.scatter(posicoes["x"], posicoes["y"], s=150 + 25 * posicoes["n"], color=cor,
                  edgecolors=SUPERFICIE, linewidth=2, zorder=2, ax=ax)
    for nome, p in posicoes.iterrows():
        pitch.annotate(_sobrenome(nome), (p["x"], p["y"] - 4.5), ax=ax, ha="center", fontsize=8,
                       color=TINTA, zorder=3, path_effects=CONTORNO)
    ax.set_title(f"Rede de passes: {time} (até o minuto {limite:.0f})", fontsize=13)
    ax.annotate(f"Círculo = passes certos · linha = pares com {min_passes}+ passes · ataque →",
                xy=(0.5, -0.02), xycoords="axes fraction", ha="center", va="top", fontsize=9, color=TINTA_2)
    return fig


def heatmap_acoes(eventos, titulo, tipo="grade"):
    pitch = _campo(line_zorder=2)
    fig, ax = pitch.draw(figsize=(10, 7))
    eventos = eventos.dropna(subset=["x", "y"])
    if tipo == "densidade" and len(eventos) > 2:
        pitch.kdeplot(eventos["x"], eventos["y"], ax=ax, fill=True, levels=60, thresh=0.05, cmap=AZUIS)
    else:
        estat = pitch.bin_statistic(eventos["x"], eventos["y"], statistic="count", bins=(6, 5), normalize=True)
        pitch.heatmap(estat, ax=ax, cmap=AZUIS, edgecolors=SUPERFICIE)
        pitch.label_heatmap(estat, ax=ax, str_format="{:.0%}", fontsize=10, color=TINTA,
                            ha="center", va="center", exclude_zeros=True,
                            path_effects=CONTORNO)
    ax.set_title(f"{titulo} ({len(eventos)} ações)", fontsize=13)
    ax.annotate("Ataque →", xy=(0.99, 1.0), xycoords="axes fraction", ha="right", va="bottom",
                fontsize=9, color=TINTA_2)
    return fig


def mapa_pressoes(pressoes, titulo):
    pitch = _campo(positional=True, shade_middle=True, positional_color=GRADE, line_zorder=2)
    fig, ax = pitch.draw(figsize=(10, 7))
    pressoes = pressoes.dropna(subset=["x", "y"])
    estat = pitch.bin_statistic_positional(pressoes["x"], pressoes["y"], statistic="count",
                                           positional="full", normalize=True)
    pitch.heatmap_positional(estat, ax=ax, cmap=AZUIS, edgecolors=SUPERFICIE)
    pitch.label_heatmap(estat, ax=ax, str_format="{:.0%}", fontsize=10, color=TINTA,
                        ha="center", va="center", exclude_zeros=True,
                            path_effects=CONTORNO)
    ax.set_title(f"{titulo} ({len(pressoes)} pressões, zonas do jogo de posição)", fontsize=13)
    return fig


def radar_comparacao(parametros, valores_a, valores_b, maximos, nomes, cores):
    radar = Radar(parametros, [0] * len(parametros), [m if m > 0 else 1 for m in maximos],
                  round_int=[False] * len(parametros), num_rings=4, ring_width=1, center_circle_radius=1)
    fig, ax = radar.setup_axis(figsize=(8, 8))
    radar.draw_circles(ax=ax, facecolor="#f0efec", edgecolor=GRADE)
    _, _, vertices_a, vertices_b = radar.draw_radar_compare(
        valores_a, valores_b, ax=ax,
        kwargs_radar={"facecolor": cores[0], "alpha": 0.45},
        kwargs_compare={"facecolor": cores[1], "alpha": 0.45},
    )
    ax.scatter(vertices_a[:, 0], vertices_a[:, 1], c=cores[0], edgecolors=SUPERFICIE, s=60, zorder=3)
    ax.scatter(vertices_b[:, 0], vertices_b[:, 1], c=cores[1], edgecolors=SUPERFICIE, s=60, zorder=3)
    radar.draw_range_labels(ax=ax, fontsize=9, color=APAGADO)
    radar.draw_param_labels(ax=ax, fontsize=11, color=TINTA)
    _legenda(ax, [(nomes[0], cores[0], "o", "", None), (nomes[1], cores[1], "o", "", None)],
             loc="upper center", bbox_to_anchor=(0.5, 1.06), fontsize=11)
    return fig


def pizza_jogador(parametros, valores, cor, titulo):
    pizza = PyPizza(params=parametros, background_color=SUPERFICIE, straight_line_color=GRADE,
                    last_circle_color=LINHAS_CAMPO, other_circle_color=GRADE, other_circle_ls="-")
    fig, _ = pizza.make_pizza(
        valores, figsize=(7, 7.5), param_location=110,
        kwargs_slices=dict(facecolor=cor, edgecolor=SUPERFICIE, linewidth=2, zorder=2),
        kwargs_params=dict(color=TINTA, fontsize=10, va="center"),
        kwargs_values=dict(color=TINTA, fontsize=9, zorder=3,
                           bbox=dict(edgecolor=LINHAS_CAMPO, facecolor=SUPERFICIE, boxstyle="round,pad=0.2")),
    )
    fig.text(0.5, 0.97, titulo, ha="center", fontsize=13, fontweight="bold")
    fig.text(0.5, 0.935, "Percentil entre os jogadores da partida (0 a 100)", ha="center", fontsize=9,
             color=TINTA_2)
    return fig


def xg_acumulado(serie, times, cores):
    fig, ax = plt.subplots(figsize=(10, 4.5))
    fim = max(serie["tempo"].max() if len(serie) else 90, 90)
    for time, cor in zip(times, cores):
        s = serie[serie["team"] == time]
        x = np.concatenate([[0], s["tempo"], [fim]])
        y = np.concatenate([[0], s["xg_acumulado"], [s["xg_acumulado"].max() if len(s) else 0]])
        ax.step(x, y, where="post", color=cor, linewidth=2, label=f"{time} ({y[-1]:.2f} xG)")
        gols = s[s["gol"]]
        ax.scatter(gols["tempo"], gols["xg_acumulado"], s=90, color=cor, edgecolors=SUPERFICIE,
                   linewidth=2, zorder=3)
        for j, (_, g) in enumerate(gols.iterrows()):
            ax.annotate(f"{_sobrenome(g['player'])} {_minuto(g)}", (g["tempo"], g["xg_acumulado"]),
                        xytext=(-6, 8 if j % 2 == 0 else -14), textcoords="offset points", ha="right",
                        fontsize=8, color=TINTA_2)
    for minuto in (45, 90, 105):
        if minuto < fim:
            ax.axvline(minuto, color=GRADE, linewidth=1, zorder=0)
    ax.set_xlabel("Minuto")
    ax.set_ylabel("xG acumulado")
    ax.set_xlim(0, fim + 1)
    ax.grid(axis="y")
    ax.legend(loc="upper left")
    ax.set_title("Corrida de xG (pontos = gols)")
    return fig


def dispersao_passes_xg(tab, times, cores, destaques=5):
    df = tab.assign(criacao=tab["xg"] + tab["xa"]).reset_index()
    fig, ax = plt.subplots(figsize=(10, 5.5))
    sns.scatterplot(data=df, x="passes", y="criacao", hue="time", hue_order=times, palette=cores,
                    size="indice", sizes=(40, 400), alpha=0.85, edgecolor=SUPERFICIE, ax=ax)
    for _, linha in df.nlargest(destaques, "indice").iterrows():
        ax.annotate(linha["jogador"], (linha["passes"], linha["criacao"]), xytext=(6, 4),
                    textcoords="offset points", fontsize=8, color=TINTA_2)
    ax.set_xlabel("Passes tentados")
    ax.set_ylabel("xG + xA (participação em chances)")
    ax.set_title("Volume de passe x participação em chances")
    ax.grid(True)
    ax.legend(bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=8, title=None)
    return fig


def barras_contribuicao(contrib, times_jogadores):
    df = contrib.iloc[::-1]
    altura = 0.45 * len(df) + 1.5
    fig, ax = plt.subplots(figsize=(10, altura))
    esquerda = np.zeros(len(df))
    for cor, familia in zip(CATEGORICAS[2:], df.columns):
        ax.barh(df.index, df[familia], left=esquerda, color=cor, edgecolor=SUPERFICIE, linewidth=2,
                height=0.7, label=familia)
        esquerda += df[familia].to_numpy()
    for i, total in enumerate(esquerda):
        ax.text(total + 0.8, i, f"{total:.1f}", va="center", fontsize=9, color=TINTA)
    ax.set_yticks(range(len(df)), [f"{nome} ({times_jogadores[nome]})" for nome in df.index])
    ax.set_xlabel("Índice de decisão (0 a 100)")
    ax.set_title("Quem decidiu a partida? Composição do índice", pad=28)
    ax.grid(axis="x")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=len(df.columns), fontsize=9)
    return fig


def heatmap_correlacao(tab, colunas, rotulos):
    corr = tab[colunas].rename(columns=rotulos).corr()
    fig, ax = plt.subplots(figsize=(9, 7))
    mascara = np.triu(np.ones_like(corr, dtype=bool), k=1)
    sns.heatmap(corr, mask=mascara, cmap=DIVERGENTE, vmin=-1, vmax=1, annot=True, fmt=".2f",
                annot_kws={"fontsize": 8}, linewidths=2, linecolor=SUPERFICIE, cbar_kws={"shrink": 0.7}, ax=ax)
    ax.set_title("Correlação entre as estatísticas dos jogadores")
    return fig


def barras_comparacao(tab, jogadores, colunas, rotulos, cores):
    df = tab.loc[jogadores, colunas].rename(columns=rotulos).T.reset_index(names="estatistica")
    df = df.melt(id_vars="estatistica", var_name="jogador", value_name="valor")
    fig, ax = plt.subplots(figsize=(10, 0.6 * len(colunas) + 1.5))
    sns.barplot(data=df, y="estatistica", x="valor", hue="jogador", palette=cores, ax=ax,
                edgecolor=SUPERFICIE, linewidth=2)
    for container in ax.containers:
        ax.bar_label(container, fmt="%.2g", fontsize=8, padding=3, color=TINTA_2)
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.grid(axis="x")
    ax.legend(loc="lower right")
    return fig


def linha_do_tempo(eventos, cor):
    df = eventos.dropna(subset=["tempo"])
    ordem = df["tipo"].value_counts().index.tolist()
    fig, ax = plt.subplots(figsize=(10, 0.35 * len(ordem) + 1.5))
    sns.stripplot(data=df, x="tempo", y="tipo", order=ordem, color=cor, size=6, jitter=0.2, alpha=0.7, ax=ax)
    gols = df[df["gol"]]
    if len(gols):
        ax.scatter(gols["tempo"], [ordem.index("Chute")] * len(gols), s=160, marker="*", color=COR_GOL,
                   zorder=3, label="Gol")
        ax.legend(loc="upper right")
    ax.set_xlabel("Minuto")
    ax.set_ylabel("")
    ax.grid(axis="x")
    ax.set_title("Linha do tempo das ações")
    return fig


def regressao_chutes_gols(resumo, cor, time):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)
    for ax, x, rotulo in zip(axes, ["chutes", "xg"], ["Chutes", "xG"]):
        sns.regplot(data=resumo, x=x, y="gols", ax=ax, color=cor, scatter_kws={"s": 70, "edgecolor": SUPERFICIE})
        for _, linha in resumo.iterrows():
            ax.annotate(linha["adversario"], (linha[x], linha["gols"]), xytext=(5, 4),
                        textcoords="offset points", fontsize=8, color=TINTA_2)
        r = resumo[[x, "gols"]].corr().iloc[0, 1] if len(resumo) > 2 else np.nan
        ax.set_title(f"{rotulo} x gols (r = {r:.2f})" if pd.notna(r) else f"{rotulo} x gols")
        ax.set_xlabel(rotulo)
        ax.set_ylabel("Gols")
        ax.grid(True)
    fig.suptitle(f"{time}: cada ponto é uma partida da competição", fontweight="bold")
    fig.tight_layout()
    return fig
