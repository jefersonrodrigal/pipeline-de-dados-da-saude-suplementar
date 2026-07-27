/* Ranking de operadoras por total de beneficiarios ativos, com participacao percentual. */
USE saude_suplementar;
GO

CREATE OR ALTER VIEW rpt.vw_ranking_operadoras AS
SELECT
    f.sk_tempo,
    t.competencia,
    o.cd_operadora_ans,
    o.nm_razao_social,
    o.modalidade,
    SUM(f.qt_beneficiario_ativo) AS qt_beneficiarios_ativos,
    DENSE_RANK() OVER (PARTITION BY f.sk_tempo ORDER BY SUM(f.qt_beneficiario_ativo) DESC) AS ranking_operadora,
    CAST(
        SUM(f.qt_beneficiario_ativo) * 100.0
        / NULLIF(SUM(SUM(f.qt_beneficiario_ativo)) OVER (PARTITION BY f.sk_tempo), 0)
        AS DECIMAL(6, 2)
    ) AS participacao_percentual
FROM fact.fato_beneficiarios f
INNER JOIN dim.dim_operadora o ON o.sk_operadora = f.sk_operadora
INNER JOIN dim.dim_tempo t ON t.sk_tempo = f.sk_tempo
GROUP BY f.sk_tempo, t.competencia, o.cd_operadora_ans, o.nm_razao_social, o.modalidade;
GO
