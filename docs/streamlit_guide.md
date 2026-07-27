# Guia da Aplicação Streamlit

## Como rodar

```bash
streamlit run app/streamlit_app.py
```

Acesse `http://localhost:8501`. Requer que `python -m src.main --stage all` já tenha
sido executado ao menos uma vez (senão as páginas mostram avisos de "nenhum dado
carregado ainda", não erros).

## Estrutura

```
app/
├── streamlit_app.py        # Home: apresentação + status do pipeline
├── pages/                  # Descoberta automática pelo Streamlit (prefixo NN_)
├── components/              # Widgets reutilizáveis (filtros, KPIs, badges)
├── charts/                  # Construtores de gráficos Plotly (paleta validada)
├── repositories/             # Acesso a dados (somente leitura, via rpt.*)
├── services/                 # DashboardService (combina repositórios)
├── config/                    # Reexporta src/config (fonte única de verdade)
└── utils/                      # Formatação pt-BR
```

## Páginas

| Página | Conteúdo | Filtros |
|---|---|---|
| **Visão Executiva** | Cards de KPI (beneficiários, estabelecimentos, operadoras, estados cobertos, razão, variação, status do pipeline), evolução mensal, ranking de estados | Competência |
| **Beneficiários** | Evolução mensal, distribuição por município, participação por operadora (abas) | Competência, UF |
| **Rede Assistencial** | Estabelecimentos por tipo, por estado/município, razão beneficiários/estabelecimento | Competência, UF |
| **Cobertura Regional** | Distribuição das classificações, ranking de risco, tabela detalhada com badge de classificação | Competência, UF |
| **Operadoras** | Ranking, concentração de mercado (top 5), participação por região, evolução de uma operadora específica | Competência |
| **Qualidade dos Dados** | Resumo geral (processados/aceitos/rejeitados), histórico de execuções, regras mais violadas | Botão de atualização manual do cache |
| **Exploração dos Dados** | Seleção de dataset (12 views), filtros dinâmicos por coluna, ordenação, seleção de colunas, resumo estatístico, download CSV | Dataset, filtros por coluna |

Cada página trata explicitamente: ausência de dados (`st.info`, nunca uma tela em
branco), banco indisponível (`DatabaseUnavailableError` → `st.error` amigável, sem
detalhes de infraestrutura) e formatação pt-BR de números/datas (`app/utils/formatting.py`).

## Estratégia de cache

- **`st.cache_resource`**: o engine SQLAlchemy (`app/repositories/base.py::get_reader_engine`)
  — uma conexão/pool por processo, nunca recriada a cada rerender.
- **`st.cache_data(ttl=STREAMLIT_CACHE_TTL_SECONDS)`**: toda função de repositório que
  retorna um DataFrame, chaveada pelos parâmetros da consulta (ex.: `sk_tempo`, `cd_uf`).
  TTL configurável via `.env` (default 300s).
- **Atualização manual**: a página "Qualidade dos Dados" expõe um botão "🔄 Atualizar
  dados" que chama `st.cache_data.clear()` e força `st.rerun()` — útil logo após rodar
  o pipeline manualmente.

Por que os repositórios usam **funções de módulo** cacheadas (não métodos de instância
diretamente decorados): `st.cache_data` precisa que os argumentos sejam hasheáveis de
forma estável para formar a chave de cache; um objeto `Engine` do SQLAlchemy passado
como argumento não é uma chave de cache confiável. A solução (padrão recomendado pelo
Streamlit) é manter o engine fora da assinatura da função cacheada — buscado
internamente via `get_reader_engine()` (que por sua vez é `cache_resource`, praticamente
gratuito de chamar a cada rerender).

## Filtros globais

`app/components/filters.py` centraliza a leitura de "períodos disponíveis" e "estados
disponíveis" (evita duplicar essas consultas em cada página). Cada página decide quais
filtros mostrar e onde (a maioria usa a sidebar); `active_filters_caption()` exibe um
resumo textual dos filtros ativos no topo do conteúdo.

## Segurança na interface

- Nenhuma página imprime a connection string, senha ou host do banco — verificado
  automaticamente em `tests/streamlit/test_pages.py::test_page_never_renders_raw_credentials`.
- Todas as consultas são parametrizadas (ver `docs/security.md`).
- A conexão usada pela aplicação é sempre `dashboard_reader` (somente leitura, restrita
  ao schema `rpt`) — nunca `etl_writer`.
