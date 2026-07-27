/*
    Classificacao EXPLORATORIA de cobertura assistencial por municipio.

    Os limiares (2.000 e 5.000 beneficiarios por estabelecimento) sao
    heuristicas definidas para fins de demonstracao/priorizacao neste
    projeto - NAO sao um padrao regulatorio da ANS/Ministerio da Saude nem
    devem ser lidos como diagnostico. Documentado tambem em
    docs/business_rules.md e reforcado na pagina "Cobertura Regional" do
    Streamlit (ver app/pages/04_cobertura_regional.py).
*/
USE saude_suplementar;
GO

CREATE OR ALTER VIEW rpt.vw_cobertura_regional AS
SELECT
    *,
    CASE
        WHEN qt_estabelecimentos = 0 THEN 'Cobertura crítica'
        WHEN beneficiarios_por_estabelecimento >= 5000 THEN 'Cobertura crítica'
        WHEN beneficiarios_por_estabelecimento >= 2000 THEN 'Atenção'
        ELSE 'Cobertura adequada'
    END AS classificacao_cobertura
FROM rpt.vw_razao_beneficiarios_estabelecimento;
GO
