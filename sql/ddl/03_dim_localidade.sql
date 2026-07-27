/*
    03_dim_localidade.sql
    Dimensao conformada de localidade (municipio + UF + regiao), compartilhada
    entre fato_beneficiarios e fato_rede_assistencial.

    A linha sk_localidade = -1 e uma linha sentinela ("Nao identificado /
    Exterior") usada quando o codigo de municipio da origem e invalido,
    ausente, ou pertence ao registro "XX" que a ANS usa para beneficiarios
    fora do Brasil / nao identificados. Isso evita LEFT JOIN NULL em
    consultas analiticas (tecnica padrao de modelagem dimensional).
*/
SET NOCOUNT ON;
USE saude_suplementar;
GO

IF OBJECT_ID('dim.dim_localidade', 'U') IS NULL
BEGIN
    CREATE TABLE dim.dim_localidade
    (
        sk_localidade       INT             NOT NULL IDENTITY(1,1),
        cd_municipio_ibge   VARCHAR(7)       NOT NULL,   -- codigo IBGE (6 ou 7 digitos conforme fonte)
        nm_municipio        VARCHAR(120)    NOT NULL,
        cd_uf               CHAR(2)         NOT NULL,
        nm_uf               VARCHAR(40)     NOT NULL,
        regiao              VARCHAR(20)     NOT NULL,

        CONSTRAINT pk_dim_localidade PRIMARY KEY NONCLUSTERED (sk_localidade),
        CONSTRAINT uq_dim_localidade_municipio UNIQUE (cd_municipio_ibge, cd_uf)
    );

    -- Indice clustered por UF+municipio: a maioria das consultas analiticas
    -- filtra/agrupa por regiao geografica antes de qualquer outra coisa.
    CREATE CLUSTERED INDEX ix_dim_localidade_uf_municipio
        ON dim.dim_localidade (cd_uf, nm_municipio);

    CREATE NONCLUSTERED INDEX ix_dim_localidade_regiao
        ON dim.dim_localidade (regiao);

    PRINT 'Tabela dim.dim_localidade criada.';
END
GO

-- Linha sentinela para localidade nao identificada / exterior.
SET IDENTITY_INSERT dim.dim_localidade ON;
IF NOT EXISTS (SELECT 1 FROM dim.dim_localidade WHERE sk_localidade = -1)
BEGIN
    INSERT INTO dim.dim_localidade
        (sk_localidade, cd_municipio_ibge, nm_municipio, cd_uf, nm_uf, regiao)
    VALUES
        (-1, '0000000', 'Nao identificado / Exterior', 'XX', 'Nao informado', 'Nao informado');
END
SET IDENTITY_INSERT dim.dim_localidade OFF;
GO
