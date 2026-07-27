/* Variacao percentual de beneficiarios ativos, periodo a periodo, por UF. */
USE saude_suplementar;
GO

CREATE OR ALTER VIEW rpt.vw_variacao_percentual_periodos AS
SELECT
    sk_tempo,
    competencia,
    cd_uf,
    nm_uf,
    regiao,
    qt_beneficiarios_ativos,
    LAG(qt_beneficiarios_ativos) OVER (PARTITION BY cd_uf ORDER BY sk_tempo) AS qt_beneficiarios_periodo_anterior,
    CASE
        WHEN LAG(qt_beneficiarios_ativos) OVER (PARTITION BY cd_uf ORDER BY sk_tempo) > 0 THEN
            CAST(
                (qt_beneficiarios_ativos - LAG(qt_beneficiarios_ativos) OVER (PARTITION BY cd_uf ORDER BY sk_tempo)) * 100.0
                / LAG(qt_beneficiarios_ativos) OVER (PARTITION BY cd_uf ORDER BY sk_tempo)
                AS DECIMAL(6, 2)
            )
    END AS variacao_percentual
FROM rpt.vw_beneficiarios_por_estado;
GO
