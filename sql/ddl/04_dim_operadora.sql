/*
    04_dim_operadora.sql
    Dimensao de operadoras de planos de saude, com suporte a SCD Tipo 2
    (Slowly Changing Dimension): quando a razao social, modalidade ou UF de
    uma operadora muda entre cargas do cadastro ANS, a linha vigente e
    "fechada" (dt_fim_vigencia preenchida, fl_vigente = 0) e uma nova linha
    e inserida com fl_vigente = 1. Isso preserva o historico para analises
    de series temporais que atravessam mudancas cadastrais.

    sk_operadora = -1 e a linha sentinela para "Operadora nao cadastrada",
    usada quando um registro de beneficiarios referencia um CD_OPERADORA que
    nao existe no cadastro de operadoras ativas (ver regra de qualidade
    "registros de operadoras inexistentes", docs/business_rules.md).
*/
SET NOCOUNT ON;
USE saude_suplementar;
GO

IF OBJECT_ID('dim.dim_operadora', 'U') IS NULL
BEGIN
    CREATE TABLE dim.dim_operadora
    (
        sk_operadora        BIGINT          NOT NULL IDENTITY(1,1),
        cd_operadora_ans     VARCHAR(10)     NOT NULL,   -- registro ANS (natural key)
        nr_cnpj              VARCHAR(14)     NULL,
        nm_razao_social      VARCHAR(200)    NOT NULL,
        nm_fantasia          VARCHAR(200)    NULL,
        modalidade           VARCHAR(60)     NULL,
        nm_municipio_sede    VARCHAR(120)    NULL,
        sg_uf_sede           CHAR(2)         NULL,
        dt_registro_ans      DATE            NULL,
        dt_inicio_vigencia   DATE            NOT NULL,
        dt_fim_vigencia      DATE            NULL,
        fl_vigente           BIT             NOT NULL DEFAULT (1),
        dh_carga             DATETIME2(0)    NOT NULL DEFAULT SYSUTCDATETIME(),

        CONSTRAINT pk_dim_operadora PRIMARY KEY NONCLUSTERED (sk_operadora),
        CONSTRAINT uq_dim_operadora_vigencia UNIQUE (cd_operadora_ans, dt_inicio_vigencia)
    );

    CREATE CLUSTERED INDEX ix_dim_operadora_codigo
        ON dim.dim_operadora (cd_operadora_ans, fl_vigente DESC);

    -- Indice filtrado: acelera o caso de uso mais comum (achar a versao
    -- vigente de uma operadora) sem varrer o historico completo.
    CREATE UNIQUE NONCLUSTERED INDEX ux_dim_operadora_vigente
        ON dim.dim_operadora (cd_operadora_ans)
        WHERE fl_vigente = 1;

    PRINT 'Tabela dim.dim_operadora criada.';
END
GO

SET IDENTITY_INSERT dim.dim_operadora ON;
IF NOT EXISTS (SELECT 1 FROM dim.dim_operadora WHERE sk_operadora = -1)
BEGIN
    INSERT INTO dim.dim_operadora
        (sk_operadora, cd_operadora_ans, nm_razao_social, modalidade,
         dt_inicio_vigencia, fl_vigente)
    VALUES
        (-1, 'N/A', 'Operadora nao cadastrada no cadastro ANS', 'Nao informado',
         '1900-01-01', 1);
END
SET IDENTITY_INSERT dim.dim_operadora OFF;
GO
