# src/repositories

Não utilizado neste projeto: o pipeline (`src/`) acessa o SQL Server diretamente através
de `src/load/` (staging, upsert, MERGE) e `src/services/` (aggregate, views,
export_analytics) — não há necessidade de uma camada de repositório adicional no lado
da carga, que já é escrita a propósito para SQL Server e usa transações explícitas.

A camada de repositórios (padrão `Repository`, consultas parametrizadas, cache) existe
do lado da **aplicação Streamlit**, em `app/repositories/` — ver
`docs/streamlit_guide.md`. Esta pasta é mantida vazia (com este README) apenas para
preservar a árvore de diretórios descrita na seção 19 do briefing.
