from server.models import Transaction, TransactionIndex
from tqdm import tqdm
from pony import orm

with orm.db_session:
    transactions = Transaction.select()

    for transaction in tqdm(transactions):
        indexes = {}

        for vout in transaction.outputs:
            if vout.currency not in indexes:
                indexes[vout.currency] = 0

            indexes[vout.currency] += vout.amount

        for currency in indexes:
            if TransactionIndex.get(currency=currency, transaction=transaction):
                continue

            TransactionIndex(**{
                "created": transaction.created,
                "amount": indexes[currency],
                "transaction": transaction,
                "currency": currency,
            })

        orm.commit()
