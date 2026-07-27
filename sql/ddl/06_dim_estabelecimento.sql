/*
    06_dim_estabelecimento.sql
    Dimensao de estabelecimentos de saude (CNES), com SCD Tipo 2 pelo mesmo
    motivo de dim_operadora: um estabelecimento pode mudar de tipo, endereco
    ou municipio de registro ao longo do tempo.

    sk_estabelecimento = -1 -> sentinela "Estabelecimento nao identificado".
*/
SET NOCOUNT ON;
USE saude_suplementar;
GO

IF OBJECT_ID('dim.dim_estabelecimento', 'U') IS NULL
BEGIN
    CREATE TABLE dim.dim_estabelecimento
    (
        sk_estabelecimento      BIGINT       NOT NULL IDENTITY(1,1),
        cd_cnes                 VARCHAR(10)  NOT NULL,   -- natural key
        nm_estabelecimento      VARCHAR(200) NOT NULL,
        sk_tipo_estabelecimento INT          NOT NULL,
        sk_localidade           INT          NOT NULL,
        dt_inicio_vigencia      DATE         NOT NULL,
        dt_fim_vigencia         DATE         NULL,
        fl_vigente              BIT          NOT NULL DEFAULT (1),
        dh_carga                DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),

        CONSTRAINT pk_dim_estabelecimento PRIMARY KEY NONCLUSTERED (sk_estabelecimento),
        CONSTRAINT uq_dim_estabelecimento_vigencia UNIQUE (cd_cnes, dt_inicio_vigencia),
        CONSTRAINT fk_dim_estabelecimento_tipo FOREIGN KEY (sk_tipo_estabelecimento)
            REFERENCES dim.dim_tipo_estabelecimento (sk_tipo_estabelecimento),
        CONSTRAINT fk_dim_estabelecimento_localidade FOREIGN KEY (sk_localidade)
            REFERENCES dim.dim_localidade (sk_localidade)
    );

    CREATE CLUSTERED INDEX ix_dim_estabelecimento_cnes
        ON dim.dim_estabelecimento (cd_cnes, fl_vigente DESC);

    CREATE UNIQUE NONCLUSTERED INDEX ux_dim_estabelecimento_vigente
        ON dim.dim_estabelecimento (cd_cnes)
        WHERE fl_vigente = 1;

    CREATE NONCLUSTERED INDEX ix_dim_estabelecimento_localidade
        ON dim.dim_estabelecimento (sk_localidade);

    PRINT 'Tabela dim.dim_estabelecimento criada.';
END
GO

SET IDENTITY_INSERT dim.dim_estabelecimento ON;
IF NOT EXISTS (SELECT 1 FROM dim.dim_estabelecimento WHERE sk_estabelecimento = -1)
BEGIN
    INSERT INTO dim.dim_estabelecimento
        (sk_estabelecimento, cd_cnes, nm_estabelecimento, sk_tipo_estabelecimento,
         sk_localidade, dt_inicio_vigencia, fl_vigente)
    VALUES
        (-1, 'N/A', 'Estabelecimento nao identificado', -1, -1, '1900-01-01', 1);
END
SET IDENTITY_INSERT dim.dim_estabelecimento OFF;
GO
