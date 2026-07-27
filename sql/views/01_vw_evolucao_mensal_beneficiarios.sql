/* Evolucao mensal do total de beneficiarios ativos (nivel Brasil). */
USE saude_suplementar;
GO

CREATE OR ALTER VIEW rpt.vw_evolucao_mensal_beneficiarios AS
WITH mensal AS (
    SELECT
        f.sk_tempo,
        t.competencia,
        t.ano_mes_extenso,
        SUM(f.qt_beneficiario_ativo) AS qt_beneficiarios_ativos
    FROM fact.fato_beneficiarios f
    INNER JOIN dim.dim_tempo t ON t.sk_tempo = f.sk_tempo
    GROUP BY f.sk_tempo, t.competencia, t.ano_mes_extenso
)
SELECT
    sk_tempo,
    competencia,
    ano_mes_extenso,
    qt_beneficiarios_ativos,
    LAG(qt_beneficiarios_ativos) OVER (ORDER BY sk_tempo) AS qt_beneficiarios_mes_anterior,
    qt_beneficiarios_ativos - LAG(qt_beneficiarios_ativos) OVER (ORDER BY sk_tempo) AS variacao_absoluta,
    CASE
        WHEN LAG(qt_beneficiarios_ativos) OVER (ORDER BY sk_tempo) > 0 THEN
            CAST((qt_beneficiarios_ativos - LAG(qt_beneficiarios_ativos) OVER (ORDER BY sk_tempo)) * 100.0
                 / LAG(qt_beneficiarios_ativos) OVER (ORDER BY sk_tempo) AS DECIMAL(6, 2))
    END AS variacao_percentual
FROM mensal;
GO
