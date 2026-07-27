/* Estabelecimentos de saude por tipo (Hospital Geral, UPA, UBS, etc.). */
USE saude_suplementar;
GO

CREATE OR ALTER VIEW rpt.vw_estabelecimentos_por_tipo AS
SELECT
    r.sk_tempo,
    t.competencia,
    tp.cd_tipo_estabelecimento,
    tp.ds_tipo_estabelecimento,
    SUM(r.qt_estabelecimento) AS qt_estabelecimentos
FROM fact.fato_rede_assistencial r
INNER JOIN dim.dim_tipo_estabelecimento tp ON tp.sk_tipo_estabelecimento = r.sk_tipo_estabelecimento
INNER JOIN dim.dim_tempo t ON t.sk_tempo = r.sk_tempo
GROUP BY r.sk_tempo, t.competencia, tp.cd_tipo_estabelecimento, tp.ds_tipo_estabelecimento;
GO
