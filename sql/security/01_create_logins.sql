/*
    01_create_logins.sql
    Cria os dois logins de aplicacao com o principio de menor privilegio:

        etl_writer        -> usado exclusivamente pelo pipeline (src/load).
                              Le/escreve em stg, dim, fact, aud, rej.
        dashboard_reader   -> usado exclusivamente pelo Streamlit (app/).
                              Somente SELECT nas views do schema rpt.

    As senhas NUNCA sao gravadas neste arquivo. Elas sao passadas como
    variaveis sqlcmd na hora da execucao, e devem vir de variaveis de
    ambiente (ver Makefile, alvo `make db-security`).

    Uso:
        sqlcmd -S localhost -E -C -d saude_suplementar \
            -v EtlWriterPassword="$SQLSERVER_PASSWORD" \
            -v DashboardReaderPassword="$SQLSERVER_READONLY_PASSWORD" \
            -i sql/security/01_create_logins.sql
*/
SET NOCOUNT ON;
USE master;
GO

IF NOT EXISTS (SELECT 1 FROM sys.server_principals WHERE name = 'etl_writer')
BEGIN
    DECLARE @sqlEtl NVARCHAR(500) =
        N'CREATE LOGIN etl_writer WITH PASSWORD = ''$(EtlWriterPassword)'', CHECK_POLICY = ON;';
    EXEC sp_executesql @sqlEtl;
    PRINT 'Login etl_writer criado.';
END
ELSE
BEGIN
    PRINT 'Login etl_writer ja existe. Nenhuma acao necessaria.';
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.server_principals WHERE name = 'dashboard_reader')
BEGIN
    DECLARE @sqlReader NVARCHAR(500) =
        N'CREATE LOGIN dashboard_reader WITH PASSWORD = ''$(DashboardReaderPassword)'', CHECK_POLICY = ON;';
    EXEC sp_executesql @sqlReader;
    PRINT 'Login dashboard_reader criado.';
END
ELSE
BEGIN
    PRINT 'Login dashboard_reader ja existe. Nenhuma acao necessaria.';
END
GO

USE saude_suplementar;
GO

IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = 'etl_writer')
BEGIN
    CREATE USER etl_writer FOR LOGIN etl_writer;
    PRINT 'Usuario etl_writer criado no banco saude_suplementar.';
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = 'dashboard_reader')
BEGIN
    CREATE USER dashboard_reader FOR LOGIN dashboard_reader;
    PRINT 'Usuario dashboard_reader criado no banco saude_suplementar.';
END
GO
