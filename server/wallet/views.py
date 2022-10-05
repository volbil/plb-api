"""Wallet API"""
from webargs.flaskparser import use_args
from flask import Blueprint
from pony import orm
import json

from ..methods.transaction import Transaction as NodeTransaction
from .args import history_args, addresses_args, unspent_args
from .args import broadcast_args, token_args
from ..services import TransactionService
from .args import check_args, utxo_args
from ..methods.address import Address
from ..methods.general import General
from ..services import AddressService
from ..services import OutputService
from ..services import BlockService
from ..services import TokenService
from ..methods.token import Token
from ..models import Transaction
from ..models import IPFSCache
from .utils import display_tx
from ..tools import display
from .. import utils

wallet = Blueprint("wallet", __name__, url_prefix="/wallet/")

@wallet.route("/balance/<string:address>", methods=["GET"])
@orm.db_session
def get_balance(address):
    """Return balance of address"""
    address = AddressService.get_by_address(address)
    block = BlockService.latest_block()
    result = []

    if address:
        for balance in address.balances:
            locked_time = OutputService.locked_time(
                address, block.created.timestamp(), balance.currency
            )

            locked_height = OutputService.locked_height(
                address, block.height, balance.currency
            )

            locked = locked_time + locked_height
            unspent = balance.balance - locked
            units = TokenService.get_units(balance.currency)
            ipfs = TokenService.get_ipfs(balance.currency)

            if balance.balance == 0:
                continue

            result.append({
                "currency": balance.currency,
                "balance": utils.satoshis(unspent),
                "locked": utils.satoshis(locked),
                "units": units,
                "ipfs": ipfs
            })

    return utils.response(result)

@wallet.route("/history", methods=["POST"])
@use_args(history_args, location="json")
@orm.db_session
def get_history(args):
    """Return history of the address"""
    transactions = None
    addresses = []
    result = []

    for raw_address in args["addresses"]:
        if raw_address:
            address = AddressService.get_by_address(raw_address)
            if address:
                addresses.append(address)

    transactions = orm.left_join(
        transaction
        for transaction in Transaction for address in transaction.addresses
        if address in addresses
    ).order_by(
        orm.desc(Transaction.created)
    )

    if args["after"]:
        after = TransactionService.get_by_txid(args["after"])
        if after:
            transactions = transactions.filter(lambda t: t.created > after.created)

    if args["before"]:
        before = TransactionService.get_by_txid(args["before"])
        if before:
            transactions = transactions.filter(lambda t: t.created < before.created)

    if args["currency"]:
        transactions = transactions.filter(
            lambda t: t.has_currency(args["currency"])
        )

    transactions = transactions.limit(args["count"])

    for db_tx in transactions:
        result.append(display_tx(db_tx))

    return utils.response(result)

@wallet.route("/transaction/<string:txid>", methods=["GET"])
@orm.db_session
def get_transaction(txid):
    """Get transaction by txid"""
    if (db_tx := TransactionService.get_by_txid(txid)):
        return utils.response(display_tx(db_tx))

    data = NodeTransaction.info(txid)

    if data["error"]:
        return utils.dead_response("Transaction not found"), 404

    result = display.tx_to_wallet(data)
    return utils.response(result)

@wallet.route("/check", methods=["POST"])
@use_args(addresses_args, location="json")
@orm.db_session
def get_check(args):
    """Check if address has been used"""
    result = []

    for raw_address in args["addresses"]:
        if raw_address:
            address = AddressService.get_by_address(raw_address)
            if address:
                result.append(raw_address)

    return utils.response(result)

@wallet.route("/utxo", methods=["POST"])
@use_args(utxo_args, location="json")
@orm.db_session
def get_utxo(args):
    """Check UTXOs"""
    result = []

    for output in args["outputs"]:
        if "index" not in output or "txid" not in output:
            continue

        transaction = TransactionService.get_by_txid(output["txid"])
        if not transaction:
            continue

        vout = OutputService.get_by_prev(transaction, output["index"])
        if not vout:
            continue

        result.append({
            "txid": transaction.txid,
            "units": TokenService.get_units(vout.currency),
            "amount": utils.satoshis(vout.amount),
            "address": vout.address.address,
            "currency": vout.currency,
            "timelock": vout.timelock,
            "category": vout.category,
            "spent": vout.spent,
            "index": vout.n
        })

    return utils.response(result)

@wallet.route("/broadcast", methods=["POST"])
@use_args(broadcast_args, location="json")
def send_broadcast(args):
    """Broadcast raw transaction"""
    return NodeTransaction.broadcast(args["raw"])

@wallet.route("/decode", methods=["POST"])
@use_args(broadcast_args, location="json")
def decode_raw(args):
    """Decode raw transaction"""
    data = NodeTransaction.decode(args["raw"])

    if data["error"] is None:
        for index, vin in enumerate(data["result"]["vin"]):
            if "txid" in vin:
                vin_data = utils.make_request(
                    "getrawtransaction", [vin["txid"], True]
                )

                if vin_data["error"] is None:
                    vout = vin_data["result"]["vout"][vin["vout"]]
                    script = vout["scriptPubKey"]
                    value = utils.satoshis(
                        vout["value"]
                    )

                    if "token" in script:
                        script["token"]["decimal"] = script["token"]["amount"]

                        script["token"]["amount"] = utils.satoshis(
                            script["token"]["amount"]
                        )

                    data["result"]["vin"][index]["scriptPubKey"] = script
                    data["result"]["vin"][index]["value"] = value

        for index, vout in enumerate(data["result"]["vout"]):
            data["result"]["vout"][index]["value"] = utils.satoshis(
                vout["value"]
            )

            script = vout["scriptPubKey"]

            if "token" in script:
                script["token"]["decimal"] = script["token"]["amount"]

                script["token"]["amount"] = utils.satoshis(
                    script["token"]["amount"]
                )

            data["result"]["vout"][index]["scriptPubKey"] = script

    return data

@wallet.route("/unspent/<string:address>", methods=["GET"])
@use_args(unspent_args, location="query")
def get_unspent(args, address):
    """Get address UTXOs"""
    return Address.unspent(address, args["amount"], args["token"])

@wallet.route("/check", methods=["POST"])
@use_args(check_args, location="JSON")
def check_addresses(args):
    """Check addresses"""
    return Address.check(args["addresses"])

@wallet.route("/tokens", methods=["GET"])
@use_args(token_args, location="query")
def get_tokens(args):
    """Get tokens"""
    return Token.list(
        args["offset"], args["count"], args["search"]
    )

@wallet.route("/info", methods=["GET"])
def get_info():
    """Return chain info"""
    return General.info()

@wallet.route("/ipfs/<string:ipfs>", methods=["GET"])
@orm.db_session
def get_ipfs_cached(ipfs):
    if (entry := IPFSCache.select(
        lambda c: c.parsed and c.content and c.ipfs == ipfs
    ).first()):
        return json.loads(entry.content)

    return "Not found", 404
