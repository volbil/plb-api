from .models import Transaction
from .models import Address
from .models import Balance
from .models import Output
from .models import Input
from .models import Block
from .models import Token
from pony import orm

class BlockService(object):
    @classmethod
    def latest_block(cls):
        return Block.select().order_by(
            orm.desc(Block.height)
        ).first()

    @classmethod
    def create(cls, reward, blockhash, height, created,
               merkleroot, chainwork, version,
               weight, stake, nonce, size, bits,
               signature=None):
        return Block(
            reward=reward, blockhash=blockhash, height=height, created=created,
            merkleroot=merkleroot, chainwork=chainwork, version=version,
            weight=weight, stake=stake, nonce=nonce, size=size, bits=bits,
            signature=signature
        )

    @classmethod
    def get_by_height(cls, height):
        return Block.get(height=height)

    @classmethod
    def get_by_hash(cls, bhash):
        return Block.get(blockhash=bhash)

    @classmethod
    def blocks(cls):
        return Block.select().order_by(
            orm.desc(Block.height)
        )

    @classmethod
    def chart(cls):
        query = orm.select((b.height, len(b.transactions)) for b in Block)
        query = query.order_by(-1)
        return query[:1440]

class TransactionService(object):
    @classmethod
    def get_by_txid(cls, txid):
        return Transaction.get(txid=txid)

    @classmethod
    def create(cls, amount, txid, created, locktime, size, height, block=None,
               coinbase=False, coinstake=False):
        return Transaction(
            amount=amount, txid=txid, created=created,
            locktime=locktime, size=size, height=height,
            coinbase=coinbase, coinstake=coinstake, block=block
        )

    @classmethod
    def total_transactions(cls, currency="PLB"):
        query = orm.select((orm.count(o.transaction)) for o in Output if o.currency == currency).distinct()
        return query.first()

class InputService(object):
    @classmethod
    def create(cls, sequence, n, transaction, vout):
        return Input(
            sequence=sequence, transaction=transaction,
            vout=vout, n=n,
        )

class AddressService(object):
    @classmethod
    def get_by_address(cls, address):
        return Address.get(address=address)

    @classmethod
    def create(cls, address):
        return Address(address=address)

class BalanceService(object):
    @classmethod
    def get_by_currency(cls, address, currency):
        return Balance.get(
            address=address, currency=currency
        )

    @classmethod
    def create(cls, address, currency):
        return Balance(
            address=address, currency=currency
        )

class OutputService(object):
    @classmethod
    def get_by_prev(cls, transaction, n):
        return Output.get(transaction=transaction, n=n)

    @classmethod
    def create(cls, transaction, amount, amount_raw, category, address, raw,
               txid, n, currency="PLB", timelock=0):
        return Output(
            transaction=transaction, amount=amount, amount_raw=amount_raw,
            category=category, address=address, raw=raw, txid=txid,
            n=n, currency=currency, timelock=timelock
        )

    @classmethod
    def locked_height(cls, address, height, currency="PLB"):
        return orm.select(
            sum(o.amount) for o in Output if o.spent is False and o.address == address and o.currency == currency and o.timelock <= 500000000 and o.timelock > height
        ).first()

    @classmethod
    def locked_time(cls, address, time, currency="PLB"):
        return orm.select(
            sum(o.amount) for o in Output if o.spent is False and o.address == address and o.currency == currency and o.timelock > 500000000 and o.timelock > time
        ).first()

class TokenService(object):
    @classmethod
    def get_units(cls, currency):
        token = Token.get(name=currency)

        if not token or currency == "PLB":
            return 8

        return token.units

    @classmethod
    def get_ipfs(cls, currency):
        token = Token.get(name=currency)

        if not token or currency == "PLB":
            return None

        return token.ipfs
