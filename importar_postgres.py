import os

import psycopg2
from ofxparse import OfxParser

ARQUIVO = "extrato.ofx"

CONFIG = {
    "host": os.getenv("PG_HOST", "ep-withered-brook-b6e1uu7g-pooler.c-2.sa-east-1.aws.neon.tech"),
    "port": os.getenv("PG_PORT", "5432"),
    "dbname": os.getenv("PG_DB", "neondb"),
    "user": os.getenv("PG_USER", "neondb_owner"),
    "password": os.getenv("PG_PASSWORD", "npg_8Ka5FonXwPjx"),
}


SQL_CRIAR_TABELA = """
CREATE TABLE IF NOT EXISTS movimentacoes (
    id SERIAL PRIMARY KEY,
    data_movimentacao DATE,
    valor NUMERIC(15,2),
    descricao VARCHAR(255)
);
"""

# Guarda o identificador único do banco (FITID) para evitar duplicatas,
# já que a descrição agora é digitada e não serve mais para comparar.
SQL_ADD_FITID = """
ALTER TABLE movimentacoes ADD COLUMN IF NOT EXISTS fitid VARCHAR(100);
"""

SQL_EXISTE = "SELECT 1 FROM movimentacoes WHERE fitid = %s LIMIT 1;"

SQL_INSERIR = """
INSERT INTO movimentacoes (data_movimentacao, valor, descricao, fitid)
VALUES (%s, %s, %s, %s);
"""


def ler_ofx(caminho):
    with open(caminho, "rb") as arquivo:
        ofx = OfxParser.parse(arquivo)
    return ofx.account.statement.transactions


def pedir_descricao(t, numero, total):
    """Mostra a movimentação e pede a descrição ao usuário."""
    original = (t.memo or t.payee or "").strip()

    print(f"\n--- Movimentação {numero}/{total} ---")
    print(f"Data     : {t.date.strftime('%d/%m/%Y')}")
    print(f"Valor    : R$ {t.amount:.2f}")
    print(f"Original : {original or '(vazio)'}")

    while True:
        texto = input("Descrição (Enter mantém a original): ").strip()
        if not texto:
            texto = original
        if texto:
            return texto[:255]
        print("A descrição não pode ficar vazia.")


def main():
    transacoes = ler_ofx(ARQUIVO)
    total = len(transacoes)
    print(f"{total} movimentações encontradas no arquivo.")

    inseridas = 0
    duplicadas = 0

    conn = psycopg2.connect(**CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute(SQL_CRIAR_TABELA)
            cur.execute(SQL_ADD_FITID)

            for i, t in enumerate(transacoes, start=1):
                data = t.date.date()
                valor = t.amount
                fitid = t.id or f"{data}|{valor}|{t.memo}"

                # Bônus: se já foi gravada antes, pula sem perguntar nada
                cur.execute(SQL_EXISTE, (fitid,))
                if cur.fetchone():
                    print(f"\nMovimentação {i}/{total} já existe no banco, ignorada.")
                    duplicadas += 1
                    continue

                descricao = pedir_descricao(t, i, total)

                cur.execute(SQL_INSERIR, (data, valor, descricao, fitid))
                inseridas += 1

        conn.commit()
    except KeyboardInterrupt:
        conn.rollback()
        print("\nInterrompido. Nada foi gravado.")
        return
    except Exception as erro:
        conn.rollback()
        print(f"Erro ao gravar no banco: {erro}")
        raise
    finally:
        conn.close()

    print("\n==============================")
    print(f"Inseridas : {inseridas}")
    print(f"Duplicadas (ignoradas): {duplicadas}")


if __name__ == "__main__":
    main()