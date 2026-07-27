/*
    02_grants.sql
    Aplica o principio de menor privilegio para os dois usuarios de aplicacao.

    etl_writer:
        - SELECT/INSERT/UPDATE/DELETE nos schemas stg, dim, fact, aud, rej
        - EXECUTE em procedures desses schemas (carga/upsert)
        - NENHUM acesso a rpt (nao precisa consultar as views analiticas)

    dashboard_reader:
        - SELECT apenas no schema rpt (views analiticas)
        - NENHUM acesso direto a stg/dim/fact/aud/rej (nao deve ver dados
          crus, tabelas de auditoria detalhadas ou registros rejeitados
          identificaveis - ver docs/security.md, secao LGPD)

    Uso:
        sqlcmd -S localhost -E -C -d saude_suplementar -i sql/security/02_grants.sql
*/
SET NOCOUNT ON;
USE saude_suplementar;
GO

GRANT SELECT, INSERT, UPDATE, DELETE ON SCHEMA::stg  TO etl_writer;
GRANT SELECT, INSERT, UPDATE, DELETE ON SCHEMA::dim  TO etl_writer;
GRANT SELECT, INSERT, UPDATE, DELETE ON SCHEMA::fact TO etl_writer;
GRANT SELECT, INSERT, UPDATE, DELETE ON SCHEMA::aud  TO etl_writer;
GRANT SELECT, INSERT, UPDATE, DELETE ON SCHEMA::rej  TO etl_writer;
-- rpt tambem recebe escrita do etl_writer: alem das 10 views (somente
-- consulta), o schema hospeda rpt.tb_resumo_mensal_uf, uma tabela
-- agregada materializada pela etapa "aggregate" do pipeline (ver
-- src/services/aggregate.py). dashboard_reader continua SOMENTE LEITURA.
GRANT SELECT, INSERT, UPDATE, DELETE ON SCHEMA::rpt  TO etl_writer;
GRANT EXECUTE ON SCHEMA::stg  TO etl_writer;
GRANT EXECUTE ON SCHEMA::dim  TO etl_writer;
GRANT EXECUTE ON SCHEMA::fact TO etl_writer;
GO

GRANT SELECT ON SCHEMA::rpt TO dashboard_reader;
GO

PRINT 'Permissoes aplicadas: etl_writer (stg/dim/fact/aud/rej) e dashboard_reader (rpt, somente leitura).';
