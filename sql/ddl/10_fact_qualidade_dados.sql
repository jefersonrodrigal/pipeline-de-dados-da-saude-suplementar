/*
    10_fact_qualidade_dados.sql
    Fato de qualidade de dados. Grao: 1 linha por execucao x etapa x regra
    de qualidade avaliada. Alimenta a pagina "Qualidade dos dados" do
    Streamlit (percentual de aprovacao, regras mais violadas, evolucao).
*/
SET NOCOUNT ON;
USE saude_suplementar;
GO

IF OBJECT_ID('fact.fato_qualidade_dados', 'U') IS NULL
BEGIN
    CREATE TABLE fact.fato_qualidade_dados
    (
        id_qualidade    BIGINT          NOT NULL IDENTITY(1,1),
        id_execucao     BIGINT          NOT NULL,
        nm_etapa        VARCHAR(50)     NOT NULL,
        nm_regra        VARCHAR(100)    NOT NULL,
        ds_regra        VARCHAR(300)    NULL,
        qt_avaliada     INT             NOT NULL,
        qt_aceita       INT             NOT NULL,
        qt_rejeitada    INT             NOT NULL,
        severidade      VARCHAR(20)     NOT NULL,   -- ERROR | WARNING
        dh_avaliacao    DATETIME2(0)    NOT NULL DEFAULT SYSUTCDATETIME(),

        CONSTRAINT pk_fato_qualidade_dados PRIMARY KEY CLUSTERED (id_qualidade),
        CONSTRAINT fk_fato_qualidade_execucao FOREIGN KEY (id_execucao)
            REFERENCES aud.execucao_pipeline (id_execucao),
        CONSTRAINT ck_fato_qualidade_severidade CHECK (severidade IN ('ERROR', 'WARNING')),
        CONSTRAINT ck_fato_qualidade_qtds CHECK (
            qt_avaliada >= 0 AND qt_aceita >= 0 AND qt_rejeitada >= 0
        )
    );

    CREATE NONCLUSTERED INDEX ix_fato_qualidade_regra
        ON fact.fato_qualidade_dados (nm_regra, dh_avaliacao DESC);

    PRINT 'Tabela fact.fato_qualidade_dados criada.';
END
GO
