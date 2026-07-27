/*
    Consultas analiticas de exemplo - respondem as 12 perguntas de negocio
    da secao 12 do briefing. Podem ser rodadas diretamente via sqlcmd/SSMS
    contra o banco saude_suplementar (schema rpt para views ja prontas,
    fact/dim quando a pergunta exige algo que nenhuma view cobre).
*/

-- =============================================================================
-- 1) Qual e a evolucao mensal dos beneficiarios?
-- =============================================================================
SELECT ano_mes_extenso, qt_beneficiarios_ativos, variacao_absoluta, variacao_percentual
FROM rpt.vw_evolucao_mensal_beneficiarios
ORDER BY sk_tempo;

-- =============================================================================
-- 2) Quais estados possuem mais beneficiarios?
-- =============================================================================
SELECT TOP 10 nm_uf, regiao, qt_beneficiarios_ativos, ranking_estado
FROM rpt.vw_beneficiarios_por_estado
WHERE sk_tempo = 202412
ORDER BY ranking_estado;

-- =============================================================================
-- 3) Quais municipios possuem menos estabelecimentos PROPORCIONALMENTE
--    (maior razao de beneficiarios por estabelecimento)?
-- =============================================================================
SELECT TOP 20 nm_municipio, nm_uf, qt_beneficiarios_ativos, qt_estabelecimentos,
       beneficiarios_por_estabelecimento
FROM rpt.vw_razao_beneficiarios_estabelecimento
WHERE sk_tempo = 202412 AND qt_estabelecimentos > 0
ORDER BY beneficiarios_por_estabelecimento DESC;

-- =============================================================================
-- 4) Qual e a razao de beneficiarios por estabelecimento (nivel Brasil)?
-- =============================================================================
SELECT
    SUM(qt_beneficiarios_ativos) AS total_beneficiarios,
    SUM(qt_estabelecimentos) AS total_estabelecimentos,
    CAST(SUM(qt_beneficiarios_ativos) AS DECIMAL(14, 2)) / NULLIF(SUM(qt_estabelecimentos), 0) AS razao_brasil
FROM rpt.vw_razao_beneficiarios_estabelecimento
WHERE sk_tempo = 202412;

-- =============================================================================
-- 5) Quais operadoras apresentam maior CRESCIMENTO entre dois periodos?
--    (usa LAG via a propria fato, pois vw_ranking_operadoras e por periodo unico)
-- =============================================================================
WITH por_periodo AS (
    SELECT f.sk_tempo, o.cd_operadora_ans, o.nm_razao_social, SUM(f.qt_beneficiario_ativo) AS qt_ativos
    FROM fact.fato_beneficiarios f
    INNER JOIN dim.dim_operadora o ON o.sk_operadora = f.sk_operadora
    GROUP BY f.sk_tempo, o.cd_operadora_ans, o.nm_razao_social
),
com_variacao AS (
    SELECT *,
           LAG(qt_ativos) OVER (PARTITION BY cd_operadora_ans ORDER BY sk_tempo) AS qt_ativos_anterior
    FROM por_periodo
)
SELECT TOP 10 sk_tempo, cd_operadora_ans, nm_razao_social, qt_ativos, qt_ativos_anterior,
       qt_ativos - qt_ativos_anterior AS crescimento_absoluto
FROM com_variacao
WHERE qt_ativos_anterior IS NOT NULL
ORDER BY crescimento_absoluto DESC;

-- =============================================================================
-- 6) Quais operadoras PERDERAM beneficiarios (mesma CTE, ordenada ao contrario)
-- =============================================================================
WITH por_periodo AS (
    SELECT f.sk_tempo, o.cd_operadora_ans, o.nm_razao_social, SUM(f.qt_beneficiario_ativo) AS qt_ativos
    FROM fact.fato_beneficiarios f
    INNER JOIN dim.dim_operadora o ON o.sk_operadora = f.sk_operadora
    GROUP BY f.sk_tempo, o.cd_operadora_ans, o.nm_razao_social
),
com_variacao AS (
    SELECT *,
           LAG(qt_ativos) OVER (PARTITION BY cd_operadora_ans ORDER BY sk_tempo) AS qt_ativos_anterior
    FROM por_periodo
)
SELECT TOP 10 sk_tempo, cd_operadora_ans, nm_razao_social, qt_ativos, qt_ativos_anterior,
       qt_ativos - qt_ativos_anterior AS variacao_absoluta
FROM com_variacao
WHERE qt_ativos_anterior IS NOT NULL
ORDER BY variacao_absoluta ASC;

-- =============================================================================
-- 7) Quais regioes apresentam possivel baixa cobertura?
--    (classificacao exploratoria - ver docs/business_rules.md)
-- =============================================================================
SELECT regiao,
       COUNT(*) AS qt_municipios,
       SUM(CASE WHEN classificacao_cobertura = 'Cobertura crítica' THEN 1 ELSE 0 END) AS qt_criticos,
       CAST(SUM(CASE WHEN classificacao_cobertura = 'Cobertura crítica' THEN 1 ELSE 0 END) * 100.0
            / COUNT(*) AS DECIMAL(5, 2)) AS percentual_critico
FROM rpt.vw_cobertura_regional
WHERE sk_tempo = 202412
GROUP BY regiao
ORDER BY percentual_critico DESC;

-- =============================================================================
-- 8) Qual foi a variacao percentual de beneficiarios entre dois periodos
--    (nacional, comparando o periodo informado com o anterior)?
-- =============================================================================
SELECT ano_mes_extenso, qt_beneficiarios_ativos, qt_beneficiarios_mes_anterior, variacao_percentual
FROM rpt.vw_evolucao_mensal_beneficiarios
WHERE sk_tempo = 202412;

-- =============================================================================
-- 9) Quais tipos de estabelecimentos sao mais comuns?
-- =============================================================================
SELECT ds_tipo_estabelecimento, SUM(qt_estabelecimentos) AS total,
       RANK() OVER (ORDER BY SUM(qt_estabelecimentos) DESC) AS ranking
FROM rpt.vw_estabelecimentos_por_tipo
WHERE sk_tempo = 202412
GROUP BY ds_tipo_estabelecimento
ORDER BY total DESC;

-- =============================================================================
-- 10) Quantos registros foram rejeitados, por regra de qualidade?
-- =============================================================================
SELECT nm_regra, ds_regra, severidade,
       SUM(qt_rejeitada) AS total_rejeitados,
       SUM(qt_avaliada) AS total_avaliado,
       CAST(SUM(qt_rejeitada) * 100.0 / NULLIF(SUM(qt_avaliada), 0) AS DECIMAL(6, 2)) AS percentual_rejeicao
FROM rpt.vw_qualidade_regras
GROUP BY nm_regra, ds_regra, severidade
ORDER BY total_rejeitados DESC;

-- =============================================================================
-- 11) Qual e o tempo medio de execucao do pipeline, por etapa?
-- =============================================================================
SELECT nm_etapa,
       COUNT(*) AS qt_execucoes,
       AVG(CAST(duracao_segundos AS FLOAT)) AS duracao_media_segundos,
       MAX(duracao_segundos) AS duracao_maxima_segundos
FROM rpt.vw_qualidade_pipeline
WHERE dh_fim IS NOT NULL
GROUP BY nm_etapa
ORDER BY duracao_media_segundos DESC;

-- =============================================================================
-- 12) Quais fontes apresentam maior incidencia de erros?
-- =============================================================================
SELECT fonte,
       COUNT(*) AS qt_execucoes,
       SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) AS qt_falhas,
       CAST(SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) * 100.0
            / COUNT(*) AS DECIMAL(5, 2)) AS percentual_falha
FROM rpt.vw_qualidade_pipeline
WHERE fonte IS NOT NULL
GROUP BY fonte
ORDER BY percentual_falha DESC;
