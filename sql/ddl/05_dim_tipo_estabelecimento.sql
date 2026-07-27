/*
    05_dim_tipo_estabelecimento.sql
    Dimensao pequena, sem historico (Tipo 1 - sobrescreve), pois o tipo de
    unidade de saude (ex.: Hospital Geral, UPA, Clinica/Ambulatorio) e um
    atributo de referencia estavel no CNES.

    sk_tipo_estabelecimento = -1 -> "Nao classificado", usado quando o
    estabelecimento carregado nao informa um tipo valido (ver regra de
    qualidade "estabelecimentos sem classificacao").
*/
SET NOCOUNT ON;
USE saude_suplementar;
GO

IF OBJECT_ID('dim.dim_tipo_estabelecimento', 'U') IS NULL
BEGIN
    CREATE TABLE dim.dim_tipo_estabelecimento
    (
        sk_tipo_estabelecimento INT         NOT NULL IDENTITY(1,1),
        cd_tipo_estabelecimento VARCHAR(10) NOT NULL,
        ds_tipo_estabelecimento VARCHAR(150) NOT NULL,

        CONSTRAINT pk_dim_tipo_estabelecimento PRIMARY KEY CLUSTERED (sk_tipo_estabelecimento),
        CONSTRAINT uq_dim_tipo_estabelecimento UNIQUE (cd_tipo_estabelecimento)
    );
    PRINT 'Tabela dim.dim_tipo_estabelecimento criada.';
END
GO

SET IDENTITY_INSERT dim.dim_tipo_estabelecimento ON;
IF NOT EXISTS (SELECT 1 FROM dim.dim_tipo_estabelecimento WHERE sk_tipo_estabelecimento = -1)
BEGIN
    INSERT INTO dim.dim_tipo_estabelecimento
        (sk_tipo_estabelecimento, cd_tipo_estabelecimento, ds_tipo_estabelecimento)
    VALUES
        (-1, 'N/A', 'Nao classificado');
END
SET IDENTITY_INSERT dim.dim_tipo_estabelecimento OFF;
GO
