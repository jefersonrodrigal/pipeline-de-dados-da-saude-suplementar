/*
    View adicional (bonus, alem das 10 obrigatorias): participacao de cada
    operadora por regiao geografica - responde diretamente "quais
    operadoras possuem maior participacao por regiao?" (pagina Operadoras).
*/
USE saude_suplementar;
GO

CREATE OR ALTER VIEW rpt.vw_operadoras_por_regiao AS
SELECT
    f.sk_tempo,
    t.competencia,
    l.regiao,
    o.cd_operadora_ans,
    o.nm_razao_social,
    SUM(f.qt_beneficiario_ativo) AS qt_beneficiarios_ativos,
    RANK() OVER (PARTITION BY f.sk_tempo, l.regiao ORDER BY SUM(f.qt_beneficiario_ativo) DESC) AS ranking_na_regiao
FROM fact.fato_beneficiarios f
INNER JOIN dim.dim_operadora o ON o.sk_operadora = f.sk_operadora
INNER JOIN dim.dim_localidade l ON l.sk_localidade = f.sk_localidade
INNER JOIN dim.dim_tempo t ON t.sk_tempo = f.sk_tempo
GROUP BY f.sk_tempo, t.competencia, l.regiao, o.cd_operadora_ans, o.nm_razao_social;
GO
