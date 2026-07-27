/* Estabelecimentos de saude por municipio. */
USE saude_suplementar;
GO

CREATE OR ALTER VIEW rpt.vw_estabelecimentos_por_municipio AS
SELECT
    r.sk_tempo,
    t.competencia,
    l.cd_municipio_ibge,
    l.nm_municipio,
    l.cd_uf,
    l.nm_uf,
    l.regiao,
    SUM(r.qt_estabelecimento) AS qt_estabelecimentos
FROM fact.fato_rede_assistencial r
INNER JOIN dim.dim_localidade l ON l.sk_localidade = r.sk_localidade
INNER JOIN dim.dim_tempo t ON t.sk_tempo = r.sk_tempo
GROUP BY r.sk_tempo, t.competencia, l.cd_municipio_ibge, l.nm_municipio, l.cd_uf, l.nm_uf, l.regiao;
GO
