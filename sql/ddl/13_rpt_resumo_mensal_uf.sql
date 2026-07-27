/*
    13_rpt_resumo_mensal_uf.sql
    Tabela de agregacao pre-calculada (etapa "aggregate" do pipeline,
    distinta de "refresh_views"): consolida, por competencia x UF, o total
    de beneficiarios ativos, total de estabelecimentos e a razao entre eles.
    Evita recalcular esses agregados a cada consulta do Streamlit (cards da
    Visao Executiva) e demonstra uma camada Gold "materializada", nao
    apenas views computadas on-the-fly (ver sql/views/).
*/
SET NOCOUNT ON;
USE saude_suplementar;
GO

IF OBJECT_ID('rpt.tb_resumo_mensal_uf', 'U') IS NULL
BEGIN
    CREATE TABLE rpt.tb_resumo_mensal_uf
    (
        sk_tempo                            INT          NOT NULL,
        cd_uf                                CHAR(2)      NOT NULL,
        nm_uf                                VARCHAR(40)  NOT NULL,
        regiao                               VARCHAR(20)  NOT NULL,
        qt_beneficiarios_ativos              BIGINT       NOT NULL,
        qt_estabelecimentos                  INT          NOT NULL,
        razao_beneficiarios_por_estabelecimento DECIMAL(12, 2) NULL,
        dh_atualizacao                       DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),

        CONSTRAINT pk_rpt_resumo_mensal_uf PRIMARY KEY CLUSTERED (sk_tempo, cd_uf)
    );
    PRINT 'Tabela rpt.tb_resumo_mensal_uf criada.';
END
GO
