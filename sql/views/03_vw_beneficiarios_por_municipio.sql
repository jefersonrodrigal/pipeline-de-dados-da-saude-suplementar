/* Beneficiarios ativos por municipio. */
USE saude_suplementar;
GO

CREATE OR ALTER VIEW rpt.vw_beneficiarios_por_municipio AS
SELECT
    f.sk_tempo,
    t.competencia,
    l.cd_municipio_ibge,
    l.nm_municipio,
    l.cd_uf,
    l.nm_uf,
    l.regiao,
    SUM(f.qt_beneficiario_ativo) AS qt_beneficiarios_ativos
FROM fact.fato_beneficiarios f
INNER JOIN dim.dim_localidade l ON l.sk_localidade = f.sk_localidade
INNER JOIN dim.dim_tempo t ON t.sk_tempo = f.sk_tempo
GROUP BY f.sk_tempo, t.competencia, l.cd_municipio_ibge, l.nm_municipio, l.cd_uf, l.nm_uf, l.regiao;
GO
