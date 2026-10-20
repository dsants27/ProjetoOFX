from ofxparse import OfxParser

ARQUIVO = "extrato.ofx"


def descricao_da(t):
    return (t.memo or t.payee or "(sem descrição)").strip()


def main():
    with open(ARQUIVO, "rb") as arquivo:
        ofx = OfxParser.parse(arquivo)

    transacoes = ofx.account.statement.transactions

    print("=" * 50)
    print("EXTRATO BANCÁRIO")
    print("=" * 50)

    entradas = 0
    saidas = 0

    for t in transacoes:
        print(f"""
Data      : {t.date.strftime('%d/%m/%Y')}
Valor     : R$ {t.amount:.2f}
Descrição : {descricao_da(t)}
--------------------------------------""")

        if t.amount > 0:
            entradas += t.amount
        else:
            saidas += t.amount

    saldo = entradas + saidas

    print("\n" + "=" * 50)
    print("RESUMO")
    print("=" * 50)
    print(f"Quantidade de movimentações: {len(transacoes)}")
    print(f"Total de entradas : R$ {entradas:.2f}")
    print(f"Total de saídas   : R$ {saidas:.2f}")
    print(f"Saldo calculado   : R$ {saldo:.2f}")


if __name__ == "__main__":
    main()