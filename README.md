# Quem decidiu a partida?

Dashboard em Streamlit com dados abertos da [StatsBomb](https://github.com/statsbomb/open-data)
(via `statsbombpy`) e visualizações com `mplsoccer`, `matplotlib` e `seaborn`.

- **App publicado:** https://lbraga-dr1-at.streamlit.app
- **Repositório:** lxbraga/DR1_AT/

## Pergunta

**Quais jogadores mais decidiram o resultado de uma partida?**

Gols contam a história mais curta. O painel olha também para quem criou as chances (assistências,
xA e passes-chave), quem levou a bola para a frente (passes e conduções progressivas) e quem
defendeu (desarmes, interceptações, bloqueios, cortes e recuperações). Essas estatísticas formam o
**índice de decisão** (0 a 100): cada estatística é dividida pelo melhor valor da partida e somada
com pesos que o usuário pode ajustar.

Partida inicial: final da Copa do Mundo de 2022, Argentina 3 x 3 França (4 x 2 nos pênaltis).
Qualquer competição, temporada e partida do repositório aberto da StatsBomb pode ser escolhida.

## Páginas

| Página | Conteúdo |
|---|---|
| Visão geral | Competição, temporada, placar, estatísticas por time, top 3 do índice, tabela de eventos com filtros e download |
| Mapas da partida | Formulário de filtros, mapa de passes, mapa de chutes, rede de passes, mapa de calor e zonas de pressão |
| Jogador | Indicadores do jogador, perfil em pizza (percentis), mapa de ações, linha do tempo e eventos para download |
| Comparação | Formulário com dois jogadores, radar e barras lado a lado, totais ou por 90 minutos |
| Quem decidiu? | Pesos do índice, ranking com a composição do índice, corrida de xG, correlações e contexto na competição |

## Mapa dos itens do enunciado

| Item | Onde |
|---|---|
| 1. Ambiente virtual e bibliotecas | `venv` + `requirements.txt` (seção "Como executar") |
| 2. Organização do código | `futebol/dados.py` (carga), `futebol/metricas.py` (cálculos), `futebol/visualizacoes.py` (gráficos), `futebol/interface.py` e `futebol/estado.py` (interface), `paginas/` (telas) |
| 3. Seletores de competição, temporada, partida e jogador; layout | Barra lateral (`app.py`); páginas usam `columns`, `container`, `tabs`, `expander` e `sidebar` |
| 4. Informações básicas e DataFrame de eventos | Visão geral |
| 5.1 Mapa de passes e de chutes (mplsoccer) | Mapas da partida, abas Passes e Chutes (legenda, tamanho por xG, chute destacado com detalhes) |
| 5.2 Matplotlib e Seaborn | Quem decidiu? (ranking, corrida de xG, dispersão passes x xG+xA, correlação, regressão chutes x gols), Comparação (barras) e Jogador (linha do tempo) |
| 5.3 Outras visualizações da galeria do mplsoccer | Rede de passes, mapa de calor (grade e densidade), zonas do jogo de posição, `Radar` e `PyPizza` |
| 6.1 Seletor de jogador e botões de filtro | Jogador (seletor e `pills` por tipo de evento), Visão geral (filtros da tabela) |
| 6.2 Download CSV | Visão geral (eventos e jogadores) e Jogador (eventos do jogador) |
| 6.3 Barras de progresso e spinners | Spinners em toda carga e desenho; barra de progresso ao carregar todas as partidas de um time (Quem decidiu?) |
| 7. `st.metric` com cores | Visão geral (delta contra o adversário, cartões com a cor de cada time), Jogador (delta contra a média da partida), Mapas e Comparação |
| 8. Formulários | Mapas (time, jogador, intervalo de minutos, quantidade de passes, checkboxes), Comparação (dois jogadores, estatísticas, escala), Quem decidiu? (pesos e tamanho do ranking); caixa de texto para busca de jogador |
| 9.1 Cache | `st.cache_data` em competições, partidas, escalações, eventos e tabela de jogadores |
| 9.2 Session State | Seleções e filtros ficam em `st.session_state` e são restaurados ao voltar a cada página (`futebol/estado.py`); o expander "Estado da sessão" mostra o conteúdo |
| 10. Deploy | Links no topo deste README |

## Definições

- **xG**: probabilidade de gol do chute, calculada pela StatsBomb.
- **xA**: soma do xG dos chutes que nasceram de passes do jogador.
- **Ação progressiva**: passe certo ou condução que aproxima a bola ao menos 25% do gol adversário e
  termina no campo de ataque (escanteios e laterais não contam).
- **Ações defensivas**: desarmes, interceptações, bloqueios, cortes e recuperações de bola.
- Chutes da disputa de pênaltis ficam fora das estatísticas e aparecem só no placar.

## Como executar

Pré-requisito: Python 3.10+.

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Testes das funções de cálculo:

```bash
pip install pytest
python -m pytest tests
```
