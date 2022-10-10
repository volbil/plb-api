"""Wallet API utils"""
from pony import orm

from ..services import TokenService
from ..models import Block
from .. import utils

def display_tx(db_tx):
    """Convert db transaction object into api compatible format"""

    latest_blocks = Block.select().order_by(
        orm.desc(Block.height)
    ).first()

    output_amount = 0
    input_amount = 0
    outputs = []
    inputs = []

    for vin in db_tx.inputs:
        units = TokenService.get_units(vin.vout.currency)

        inputs.append({
            "address": vin.vout.address.address,
            "currency": vin.vout.currency,
            "amount": utils.satoshis(vin.vout.amount),
            "units": units
        })

        if vin.vout.currency == "PLB":
            input_amount += utils.satoshis(vin.vout.amount)

    for vout in db_tx.outputs:
        units = TokenService.get_units(vout.currency)

        outputs.append({
            "address": vout.address.address,
            "currency": vout.currency,
            "timelock": vout.timelock,
            "category": vout.category,
            "amount": utils.satoshis(vout.amount),
            "units": units,
            "spent": vout.spent,
            "n": vout.n
        })

        if vout.currency == "PLB":
            output_amount += utils.satoshis(vout.amount)

    return {
        "confirmations": db_tx.confirmations,
        "fee": input_amount - output_amount,
        "timestamp": int(db_tx.created.timestamp()),
        "amount": utils.satoshis(db_tx.amount),
        "height": db_tx.display_height,
        "coinstake": db_tx.coinstake,
        "coinbase": db_tx.coinbase,
        "txid": db_tx.txid,
        "size": db_tx.size,
        "outputs": outputs,
        "mempool": False,
        "inputs": inputs
    }
