/*
    01_create_schemas.sql
    Cria os schemas usados para separar responsabilidades dentro do banco
    (equivalente a uma arquitetura medalhao dentro de uma unica base):

        stg  -> staging (carga bruta antes do upsert, esvaziada a cada lote)
        dim  -> dimensoes conformadas (Analytics/Gold)
        fact -> tabelas fato (Analytics/Gold)
        aud  -> auditoria de execucao do pipeline e qualidade de dados
        rej  -> registros rejeitados pelas regras de qualidade
        rpt  -> views analiticas consumidas pelo Streamlit (unico schema
                exposto ao usuario dashboard_reader)

    Uso:
        sqlcmd -S localhost -E -C -d saude_suplementar -i sql/ddl/01_create_schemas.sql
*/
SET NOCOUNT ON;
USE saude_suplementar;
GO

DECLARE @schemas TABLE (nome SYSNAME);
INSERT INTO @schemas (nome) VALUES ('stg'), ('dim'), ('fact'), ('aud'), ('rej'), ('rpt');

DECLARE @schema SYSNAME, @sql NVARCHAR(200);
DECLARE cur CURSOR LOCAL FAST_FORWARD FOR SELECT nome FROM @schemas;
OPEN cur;
FETCH NEXT FROM cur INTO @schema;
WHILE @@FETCH_STATUS = 0
BEGIN
    IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = @schema)
    BEGIN
        SET @sql = N'CREATE SCHEMA ' + QUOTENAME(@schema) + N' AUTHORIZATION dbo;';
        EXEC sp_executesql @sql;
        PRINT 'Schema criado: ' + @schema;
    END
    FETCH NEXT FROM cur INTO @schema;
END
CLOSE cur;
DEALLOCATE cur;
GO
