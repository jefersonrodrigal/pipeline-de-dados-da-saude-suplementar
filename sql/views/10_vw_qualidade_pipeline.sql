/* Historico de execucoes do pipeline: status, duracao, volumes e percentual de aprovacao. */
USE saude_suplementar;
GO

CREATE OR ALTER VIEW rpt.vw_qualidade_pipeline AS
SELECT
    e.id_execucao,
    e.nm_pipeline,
    e.nm_etapa,
    e.dh_inicio,
    e.dh_fim,
    e.duracao_segundos,
    e.periodo_referencia,
    e.fonte,
    e.status,
    e.qt_recebida,
    e.qt_valida,
    e.qt_rejeitada,
    CASE WHEN e.qt_recebida > 0 THEN CAST(e.qt_valida * 100.0 / e.qt_recebida AS DECIMAL(6, 2)) END AS percentual_aprovacao
FROM aud.execucao_pipeline e;
GO
