/*
    Razao beneficiarios/estabelecimento por municipio. LEFT JOIN
    deliberado: municipios com beneficiarios mas ZERO estabelecimentos
    devem aparecer com qt_estabelecimentos = 0 (nao desaparecer da view) -
    e exatamente esse tipo de linha que sinaliza uma possivel lacuna de
    atendimento (ver rpt.vw_cobertura_regional).
*/
USE saude_suplementar;
GO

CREATE OR ALTER VIEW rpt.vw_razao_beneficiarios_estabelecimento AS
SELECT
    b.sk_tempo,
    b.competencia,
    b.cd_municipio_ibge,
    b.nm_municipio,
    b.cd_uf,
    b.nm_uf,
    b.regiao,
    b.qt_beneficiarios_ativos,
    ISNULL(e.qt_estabelecimentos, 0) AS qt_estabelecimentos,
    CASE
        WHEN ISNULL(e.qt_estabelecimentos, 0) = 0 THEN NULL
        ELSE CAST(b.qt_beneficiarios_ativos AS DECIMAL(14, 2)) / e.qt_estabelecimentos
    END AS beneficiarios_por_estabelecimento
FROM rpt.vw_beneficiarios_por_municipio b
LEFT JOIN rpt.vw_estabelecimentos_por_municipio e
    ON e.sk_tempo = b.sk_tempo
   AND e.cd_municipio_ibge = b.cd_municipio_ibge
   AND e.cd_uf = b.cd_uf;
GO
