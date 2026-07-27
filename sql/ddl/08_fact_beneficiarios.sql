/*
    08_fact_beneficiarios.sql
    Fato de beneficiarios. Grao: 1 linha por competencia x operadora x
    localidade x sexo x faixa etaria x tipo de vinculo x segmentacao de
    plano - o mesmo grao publicado pela ANS no arquivo de beneficiarios
    consolidados (nao ha row-level de pessoa fisica, apenas contagens).

    sexo/faixa_etaria/tipo_vinculo/segmentacao_plano sao mantidos como
    dimensoes degeneradas (atributos direto na fato) em vez de mini-
    dimensoes separadas: sao poucos valores distintos, nao mudam com o
    tempo e nao sao reutilizados por outras fatos, entao criar tabelas
    dim.dim_sexo, dim.dim_faixa_etaria etc. so adicionaria joins sem
    beneficio analitico real.

    Estrategia de carga: staging (stg.beneficiarios) -> MERGE por chave de
    grao -> fato. Ver src/load/loader.py e sql/staging/.
*/
SET NOCOUNT ON;
USE saude_suplementar;
GO

IF OBJECT_ID('fact.fato_beneficiarios', 'U') IS NULL
BEGIN
    CREATE TABLE fact.fato_beneficiarios
    (
        sk_beneficiarios        BIGINT       NOT NULL IDENTITY(1,1),
        sk_tempo                 INT          NOT NULL,
        sk_operadora             BIGINT       NOT NULL,
        sk_localidade            INT          NOT NULL,
        tp_sexo                  CHAR(1)      NULL,
        de_faixa_etaria          VARCHAR(20)  NULL,
        tipo_vinculo             VARCHAR(30)  NULL,
        segmentacao_plano        VARCHAR(60)  NULL,
        qt_beneficiario_ativo    INT          NOT NULL DEFAULT (0),
        qt_beneficiario_aderido  INT          NOT NULL DEFAULT (0),
        qt_beneficiario_cancelado INT         NOT NULL DEFAULT (0),
        id_execucao              BIGINT       NOT NULL,
        dh_carga                 DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),

        CONSTRAINT pk_fato_beneficiarios PRIMARY KEY NONCLUSTERED (sk_beneficiarios),
        CONSTRAINT fk_fato_beneficiarios_tempo FOREIGN KEY (sk_tempo)
            REFERENCES dim.dim_tempo (sk_tempo),
        CONSTRAINT fk_fato_beneficiarios_operadora FOREIGN KEY (sk_operadora)
            REFERENCES dim.dim_operadora (sk_operadora),
        CONSTRAINT fk_fato_beneficiarios_localidade FOREIGN KEY (sk_localidade)
            REFERENCES dim.dim_localidade (sk_localidade),
        CONSTRAINT fk_fato_beneficiarios_execucao FOREIGN KEY (id_execucao)
            REFERENCES aud.execucao_pipeline (id_execucao),
        CONSTRAINT ck_fato_beneficiarios_qtds CHECK (
            qt_beneficiario_ativo >= 0 AND qt_beneficiario_aderido >= 0
            AND qt_beneficiario_cancelado >= 0
        ),
        -- Chave de grao de negocio: garante idempotencia do upsert (MERGE)
        -- e impede cargas duplicadas do mesmo periodo/recorte.
        CONSTRAINT uq_fato_beneficiarios_grao UNIQUE (
            sk_tempo, sk_operadora, sk_localidade, tp_sexo, de_faixa_etaria,
            tipo_vinculo, segmentacao_plano
        )
    );

    -- Clustered por sk_tempo: quase toda consulta analitica filtra por
    -- periodo antes de agrupar por operadora/localidade.
    CREATE CLUSTERED INDEX ix_fato_beneficiarios_tempo
        ON fact.fato_beneficiarios (sk_tempo);

    CREATE NONCLUSTERED INDEX ix_fato_beneficiarios_operadora
        ON fact.fato_beneficiarios (sk_operadora, sk_tempo)
        INCLUDE (qt_beneficiario_ativo);

    CREATE NONCLUSTERED INDEX ix_fato_beneficiarios_localidade
        ON fact.fato_beneficiarios (sk_localidade, sk_tempo)
        INCLUDE (qt_beneficiario_ativo);

    PRINT 'Tabela fact.fato_beneficiarios criada.';
END
GO
