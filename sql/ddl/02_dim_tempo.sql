/*
    02_dim_tempo.sql
    Dimensao de tempo, granularidade MENSAL (competencia), pois todas as
    fontes usadas (ANS beneficiarios e CNES) publicam dados por competencia
    mensal, nao diaria.

    Chave substituta (sk_tempo) = a propria competencia no formato AAAAMM,
    como inteiro. Isso e uma "smart key" deliberada: e estavel, ordenavel,
    legivel em depuracao (202412) e evita uma tabela de lookup adicional so
    para traduzir uma data em um numero sequencial. Documentado em
    docs/architecture.md.
*/
SET NOCOUNT ON;
USE saude_suplementar;
GO

IF OBJECT_ID('dim.dim_tempo', 'U') IS NULL
BEGIN
    CREATE TABLE dim.dim_tempo
    (
        sk_tempo            INT             NOT NULL,
        competencia         DATE            NOT NULL,   -- primeiro dia do mes
        ano                 SMALLINT        NOT NULL,
        mes                 TINYINT         NOT NULL,
        nome_mes             VARCHAR(20)     NOT NULL,
        trimestre           TINYINT         NOT NULL,
        semestre            TINYINT         NOT NULL,
        ano_mes_extenso     VARCHAR(20)     NOT NULL,   -- ex.: "Dezembro/2024"

        CONSTRAINT pk_dim_tempo PRIMARY KEY CLUSTERED (sk_tempo),
        CONSTRAINT uq_dim_tempo_competencia UNIQUE (competencia),
        CONSTRAINT ck_dim_tempo_mes CHECK (mes BETWEEN 1 AND 12),
        CONSTRAINT ck_dim_tempo_trimestre CHECK (trimestre BETWEEN 1 AND 4),
        CONSTRAINT ck_dim_tempo_semestre CHECK (semestre BETWEEN 1 AND 2)
    );
    PRINT 'Tabela dim.dim_tempo criada.';
END
GO
