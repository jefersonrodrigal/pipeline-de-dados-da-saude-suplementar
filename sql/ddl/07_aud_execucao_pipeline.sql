/*
    07_aud_execucao_pipeline.sql
    Tabela de auditoria de execucao do pipeline. Cada etapa (extract,
    validate_raw, transform, validate_trusted, load, aggregate,
    refresh_views, export_analytics) grava uma linha aqui ao iniciar e
    atualiza a mesma linha ao terminar (sucesso ou falha). E a fonte de
    verdade consumida pela pagina "Qualidade dos dados" do Streamlit e pela
    view rpt.vw_qualidade_pipeline.
*/
SET NOCOUNT ON;
USE saude_suplementar;
GO

IF OBJECT_ID('aud.execucao_pipeline', 'U') IS NULL
BEGIN
    CREATE TABLE aud.execucao_pipeline
    (
        id_execucao         BIGINT          NOT NULL IDENTITY(1,1),
        nm_pipeline         VARCHAR(100)    NOT NULL,
        nm_etapa            VARCHAR(50)     NOT NULL,
        dh_inicio           DATETIME2(0)    NOT NULL,
        dh_fim              DATETIME2(0)    NULL,
        origem_arquivo      VARCHAR(300)    NULL,
        hash_arquivo        CHAR(64)        NULL,        -- SHA-256
        periodo_referencia  VARCHAR(7)      NULL,        -- AAAA-MM
        fonte               VARCHAR(20)     NULL,        -- ans | cnes
        qt_recebida         INT             NULL,
        qt_valida           INT             NULL,
        qt_rejeitada        INT             NULL,
        regra_violada       VARCHAR(200)    NULL,
        mensagem_erro       NVARCHAR(MAX)   NULL,
        status              VARCHAR(20)     NOT NULL,    -- RUNNING | SUCCESS | FAILED | PARTIAL
        duracao_segundos    AS (DATEDIFF(SECOND, dh_inicio, dh_fim)) PERSISTED,

        CONSTRAINT pk_aud_execucao_pipeline PRIMARY KEY CLUSTERED (id_execucao),
        CONSTRAINT ck_aud_execucao_status CHECK (status IN ('RUNNING', 'SUCCESS', 'FAILED', 'PARTIAL'))
    );

    CREATE NONCLUSTERED INDEX ix_aud_execucao_etapa
        ON aud.execucao_pipeline (nm_etapa, dh_inicio DESC);

    CREATE NONCLUSTERED INDEX ix_aud_execucao_periodo
        ON aud.execucao_pipeline (periodo_referencia, fonte);

    PRINT 'Tabela aud.execucao_pipeline criada.';
END
GO
