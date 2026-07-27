/*
    12_staging_tables.sql
    Tabelas de staging: recebem a carga em lote (bulk) dos arquivos Parquet
    da camada Trusted, ja com chaves substitutas resolvidas pelo Python
    (src/load/loader.py), antes do MERGE para as tabelas fato. Cada carga
    trunca e recarrega apenas o lote da execucao corrente (staging nao
    acumula historico - ver docs/architecture.md, secao "Carga").
*/
SET NOCOUNT ON;
USE saude_suplementar;
GO

IF OBJECT_ID('stg.beneficiarios', 'U') IS NULL
BEGIN
    CREATE TABLE stg.beneficiarios
    (
        id_execucao               BIGINT       NOT NULL,
        sk_tempo                   INT          NOT NULL,
        sk_operadora               BIGINT       NOT NULL,
        sk_localidade              INT          NOT NULL,
        tp_sexo                    CHAR(1)      NULL,
        de_faixa_etaria            VARCHAR(20)  NULL,
        tipo_vinculo                VARCHAR(30)  NULL,
        segmentacao_plano          VARCHAR(60)  NULL,
        qt_beneficiario_ativo      INT          NOT NULL,
        qt_beneficiario_aderido    INT          NOT NULL,
        qt_beneficiario_cancelado  INT          NOT NULL
    );
    CREATE CLUSTERED INDEX ix_stg_beneficiarios_grao
        ON stg.beneficiarios (sk_tempo, sk_operadora, sk_localidade);
    PRINT 'Tabela stg.beneficiarios criada.';
END
GO

IF OBJECT_ID('stg.operadoras', 'U') IS NULL
BEGIN
    CREATE TABLE stg.operadoras
    (
        cd_operadora_ans   VARCHAR(10)  NOT NULL,
        nr_cnpj            VARCHAR(14)  NULL,
        nm_razao_social    VARCHAR(200) NOT NULL,
        nm_fantasia        VARCHAR(200) NULL,
        modalidade         VARCHAR(60)  NULL,
        nm_municipio_sede  VARCHAR(120) NULL,
        sg_uf_sede         CHAR(2)      NULL,
        dt_registro_ans    DATE         NULL
    );
    CREATE CLUSTERED INDEX ix_stg_operadoras_codigo
        ON stg.operadoras (cd_operadora_ans);
    PRINT 'Tabela stg.operadoras criada.';
END
GO

IF OBJECT_ID('stg.estabelecimentos', 'U') IS NULL
BEGIN
    CREATE TABLE stg.estabelecimentos
    (
        cd_cnes                 VARCHAR(10)  NOT NULL,
        nm_estabelecimento      VARCHAR(200) NOT NULL,
        cd_tipo_estabelecimento VARCHAR(10)  NULL,
        ds_tipo_estabelecimento VARCHAR(150) NULL,
        cd_municipio_ibge       VARCHAR(7)   NULL,
        nm_municipio            VARCHAR(120) NULL,
        cd_uf                   CHAR(2)      NULL,
        periodo_referencia      VARCHAR(7)   NOT NULL
    );
    CREATE CLUSTERED INDEX ix_stg_estabelecimentos_codigo
        ON stg.estabelecimentos (cd_cnes);
    PRINT 'Tabela stg.estabelecimentos criada.';
END
GO
