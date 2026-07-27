/*
    View adicional (nao contabilizada entre as 10 obrigatorias, mas usada
    pela pagina "Qualidade dos dados"): detalhe por regra de qualidade
    avaliada em cada execucao - alimenta o ranking de "regras mais
    violadas" e a evolucao de erros por execucao.
*/
USE saude_suplementar;
GO

CREATE OR ALTER VIEW rpt.vw_qualidade_regras AS
SELECT
    q.id_qualidade,
    q.id_execucao,
    e.periodo_referencia,
    e.fonte,
    q.nm_etapa,
    q.nm_regra,
    q.ds_regra,
    q.severidade,
    q.qt_avaliada,
    q.qt_aceita,
    q.qt_rejeitada,
    q.dh_avaliacao
FROM fact.fato_qualidade_dados q
INNER JOIN aud.execucao_pipeline e ON e.id_execucao = q.id_execucao;
GO
