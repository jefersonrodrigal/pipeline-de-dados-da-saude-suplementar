"""Carga das tabelas fato.

fato_beneficiarios: estrategia EXPLICITA (staging -> UPDATE existentes ->
INSERT novos -> validar contagens), priorizada conforme a especificacao do
projeto por ser mais previsivel e facil de depurar/testar que um MERGE.

fato_rede_assistencial: usa o comando MERGE do SQL Server deliberadamente,
como o "caso avaliado" pedido pela especificacao. Grao (sk_tempo,
sk_estabelecimento) tem ambas as chaves sempre NOT NULL, o que evita a
armadilha mais comum do MERGE (comparacoes NULL x NULL na condicao ON nao
batem, silenciosamente duplicando linhas). Limitacoes do MERGE observadas e
mitigadas aqui:
  - "The MERGE statement attempted to UPDATE or DELETE the same row more
    than once": ocorre se a origem tiver linhas duplicadas na chave de
    junction. Mitigado porque dim.dim_estabelecimento so tem uma linha
    vigente (fl_vigente=1) por cd_cnes (unique index filtrado).
  - MERGE nao e mais rapido que UPDATE+INSERT separados no SQL Server (mito
    comum) - usado aqui por motivo didatico/arquitetural, nao performance.
  - Testado em tests/integration/test_load_facts.py (upsert + idempotencia).
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Connection

_GRAIN_JOIN = """
    f.sk_tempo = s.sk_tempo
    AND f.sk_operadora = s.sk_operadora
    AND f.sk_localidade = s.sk_localidade
    AND ISNULL(f.tp_sexo, '') = ISNULL(s.tp_sexo, '')
    AND ISNULL(f.de_faixa_etaria, '') = ISNULL(s.de_faixa_etaria, '')
    AND ISNULL(f.tipo_vinculo, '') = ISNULL(s.tipo_vinculo, '')
    AND ISNULL(f.segmentacao_plano, '') = ISNULL(s.segmentacao_plano, '')
"""


def load_fato_beneficiarios(connection: Connection, staged_count: int) -> dict[str, int]:
    """Assume que stg.beneficiarios ja foi truncada e recarregada pelo chamador.

    Retorna contagens {"atualizados": x, "inseridos": y} e valida que a soma
    bate com `staged_count` (garantindo que nenhuma linha da staging foi
    perdida ou processada duas vezes).
    """
    update_result = connection.execute(text(f"""
            UPDATE f
            SET f.qt_beneficiario_ativo = s.qt_beneficiario_ativo,
                f.qt_beneficiario_aderido = s.qt_beneficiario_aderido,
                f.qt_beneficiario_cancelado = s.qt_beneficiario_cancelado,
                f.id_execucao = s.id_execucao,
                f.dh_carga = SYSUTCDATETIME()
            FROM fact.fato_beneficiarios f
            INNER JOIN stg.beneficiarios s ON {_GRAIN_JOIN}
            """))
    updated = update_result.rowcount

    insert_result = connection.execute(text(f"""
            INSERT INTO fact.fato_beneficiarios
                (sk_tempo, sk_operadora, sk_localidade, tp_sexo, de_faixa_etaria,
                 tipo_vinculo, segmentacao_plano, qt_beneficiario_ativo,
                 qt_beneficiario_aderido, qt_beneficiario_cancelado, id_execucao)
            SELECT s.sk_tempo, s.sk_operadora, s.sk_localidade, s.tp_sexo, s.de_faixa_etaria,
                   s.tipo_vinculo, s.segmentacao_plano, s.qt_beneficiario_ativo,
                   s.qt_beneficiario_aderido, s.qt_beneficiario_cancelado, s.id_execucao
            FROM stg.beneficiarios s
            WHERE NOT EXISTS (
                SELECT 1 FROM fact.fato_beneficiarios f WHERE {_GRAIN_JOIN}
            )
            """))
    inserted = insert_result.rowcount

    if updated + inserted != staged_count:
        raise RuntimeError(
            f"Validacao de carga falhou: staging tinha {staged_count} linhas, mas "
            f"{updated} atualizadas + {inserted} inseridas = {updated + inserted}."
        )

    return {"atualizados": updated, "inseridos": inserted}


def load_fato_rede_assistencial(
    connection: Connection, sk_tempo: int, id_execucao: int
) -> dict[str, int]:
    """MERGE deliberado - ver docstring do modulo. Le de dim.dim_estabelecimento
    (ja upsertada) join stg.estabelecimentos (linhas do lote corrente)."""
    result = connection.execute(
        text("""
            MERGE fact.fato_rede_assistencial AS tgt
            USING (
                SELECT DISTINCT :sk_tempo AS sk_tempo, dst.sk_estabelecimento,
                       dst.sk_tipo_estabelecimento, dst.sk_localidade
                FROM dim.dim_estabelecimento dst
                INNER JOIN stg.estabelecimentos src ON src.cd_cnes = dst.cd_cnes
                WHERE dst.fl_vigente = 1
            ) AS src
            ON tgt.sk_tempo = src.sk_tempo AND tgt.sk_estabelecimento = src.sk_estabelecimento
            WHEN MATCHED THEN UPDATE SET
                tgt.sk_tipo_estabelecimento = src.sk_tipo_estabelecimento,
                tgt.sk_localidade = src.sk_localidade,
                tgt.id_execucao = :id_execucao,
                tgt.dh_carga = SYSUTCDATETIME()
            WHEN NOT MATCHED THEN INSERT
                (sk_tempo, sk_estabelecimento, sk_tipo_estabelecimento, sk_localidade, qt_estabelecimento, id_execucao)
                VALUES (src.sk_tempo, src.sk_estabelecimento, src.sk_tipo_estabelecimento, src.sk_localidade, 1, :id_execucao)
            OUTPUT $action AS acao;
            """),
        {"sk_tempo": sk_tempo, "id_execucao": id_execucao},
    )
    actions = [row[0] for row in result.fetchall()]
    return {
        "atualizados": actions.count("UPDATE"),
        "inseridos": actions.count("INSERT"),
    }
