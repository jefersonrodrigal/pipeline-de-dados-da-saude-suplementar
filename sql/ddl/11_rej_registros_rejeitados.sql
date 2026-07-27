/*
    11_rej_registros_rejeitados.sql
    Registros rejeitados pela camada de qualidade (Trusted), com o motivo e
    o identificador de execucao. Espelha o que tambem e gravado em arquivo
    (data/rejected/) - ver src/quality/validators.py. Guardar aqui permite
    consultar rejeicoes via SQL sem reprocessar arquivos.

    Nota LGPD: registro_json guarda a linha rejeitada tal como recebida da
    fonte publica (sem dados pessoais de beneficiarios individuais, pois a
    fonte ANS ja e agregada). Ver docs/security.md.
*/
SET NOCOUNT ON;
USE saude_suplementar;
GO

IF OBJECT_ID('rej.registros_rejeitados', 'U') IS NULL
BEGIN
    CREATE TABLE rej.registros_rejeitados
    (
        id_rejeicao     BIGINT          NOT NULL IDENTITY(1,1),
        id_execucao     BIGINT          NOT NULL,
        nm_dataset      VARCHAR(50)     NOT NULL,   -- beneficiarios | operadoras | estabelecimentos
        regra_violada   VARCHAR(200)    NOT NULL,
        motivo          NVARCHAR(500)   NOT NULL,
        registro_json   NVARCHAR(MAX)   NULL,
        dh_rejeicao     DATETIME2(0)    NOT NULL DEFAULT SYSUTCDATETIME(),

        CONSTRAINT pk_rej_registros_rejeitados PRIMARY KEY CLUSTERED (id_rejeicao),
        CONSTRAINT fk_rej_registros_execucao FOREIGN KEY (id_execucao)
            REFERENCES aud.execucao_pipeline (id_execucao)
    );

    CREATE NONCLUSTERED INDEX ix_rej_registros_regra
        ON rej.registros_rejeitados (regra_violada, dh_rejeicao DESC);

    PRINT 'Tabela rej.registros_rejeitados criada.';
END
GO
