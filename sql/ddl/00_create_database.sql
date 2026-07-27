/*
    00_create_database.sql
    Cria o banco de dados principal do projeto, caso ainda nao exista.
    Executar como usuario com permissao sysadmin/dbcreator (ex.: via Windows
    Authentication local, ou sa em um container Docker recem-criado).

    Uso:
        sqlcmd -S localhost -E -C -i sql/ddl/00_create_database.sql
*/
SET NOCOUNT ON;

IF DB_ID(N'saude_suplementar') IS NULL
BEGIN
    PRINT 'Criando banco de dados saude_suplementar...';
    -- Collation acentuada, case-insensitive: adequada para nomes de
    -- municipios/operadoras em portugues.
    CREATE DATABASE saude_suplementar
        COLLATE Latin1_General_CI_AI;
END
ELSE
BEGIN
    PRINT 'Banco de dados saude_suplementar ja existe. Nenhuma acao necessaria.';
END
GO

ALTER DATABASE saude_suplementar SET RECOVERY SIMPLE;
GO
