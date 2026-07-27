/*
    09_fact_rede_assistencial.sql
    Fato de rede assistencial (estabelecimentos de saude). Grao: 1 linha por
    competencia (periodo de referencia do cadastro CNES) x estabelecimento.
    qt_estabelecimento e sempre 1 neste grao - existe para permitir SUM()
    direto nas views/agregacoes por municipio/tipo/regiao sem precisar de
    COUNT(DISTINCT ...), o que e mais barato em consultas com GROUP BY.
*/
SET NOCOUNT ON;
USE saude_suplementar;
GO

IF OBJECT_ID('fact.fato_rede_assistencial', 'U') IS NULL
BEGIN
    CREATE TABLE fact.fato_rede_assistencial
    (
        sk_rede_assistencial    BIGINT       NOT NULL IDENTITY(1,1),
        sk_tempo                 INT          NOT NULL,
        sk_estabelecimento       BIGINT       NOT NULL,
        sk_tipo_estabelecimento  INT          NOT NULL,
        sk_localidade            INT          NOT NULL,
        qt_estabelecimento       INT          NOT NULL DEFAULT (1),
        id_execucao              BIGINT       NOT NULL,
        dh_carga                 DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),

        CONSTRAINT pk_fato_rede_assistencial PRIMARY KEY NONCLUSTERED (sk_rede_assistencial),
        CONSTRAINT fk_fato_rede_tempo FOREIGN KEY (sk_tempo)
            REFERENCES dim.dim_tempo (sk_tempo),
        CONSTRAINT fk_fato_rede_estabelecimento FOREIGN KEY (sk_estabelecimento)
            REFERENCES dim.dim_estabelecimento (sk_estabelecimento),
        CONSTRAINT fk_fato_rede_tipo FOREIGN KEY (sk_tipo_estabelecimento)
            REFERENCES dim.dim_tipo_estabelecimento (sk_tipo_estabelecimento),
        CONSTRAINT fk_fato_rede_localidade FOREIGN KEY (sk_localidade)
            REFERENCES dim.dim_localidade (sk_localidade),
        CONSTRAINT fk_fato_rede_execucao FOREIGN KEY (id_execucao)
            REFERENCES aud.execucao_pipeline (id_execucao),
        CONSTRAINT ck_fato_rede_qtd CHECK (qt_estabelecimento >= 0),
        CONSTRAINT uq_fato_rede_grao UNIQUE (sk_tempo, sk_estabelecimento)
    );

    CREATE CLUSTERED INDEX ix_fato_rede_tempo
        ON fact.fato_rede_assistencial (sk_tempo);

    CREATE NONCLUSTERED INDEX ix_fato_rede_localidade
        ON fact.fato_rede_assistencial (sk_localidade, sk_tempo)
        INCLUDE (qt_estabelecimento);

    CREATE NONCLUSTERED INDEX ix_fato_rede_tipo
        ON fact.fato_rede_assistencial (sk_tipo_estabelecimento, sk_tempo)
        INCLUDE (qt_estabelecimento);

    PRINT 'Tabela fact.fato_rede_assistencial criada.';
END
GO
