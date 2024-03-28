from ..methods.transaction import Transaction as NodeTransaction
from ..methods.general import General as NodeGeneral
from ..services import TransactionService
from webargs.flaskparser import use_args
from ..models import TransactionIndex
from ..services import AddressService
from ..services import OutputService
from .args import page_args_richlist
from ..services import BlockService
from ..models import Transaction
from .args import broadcast_args
from .args import tokens_args
from ..models import Balance
from .args import chart_args
from .args import page_args
from flask import Blueprint
from ..tools import display
from ..models import Token
from .. import utils
from pony import orm
import math

from decimal import Decimal

db = Blueprint("db", __name__, url_prefix="/v2/")


@db.route("/latest", methods=["GET"])
@orm.db_session
def info():
    block = BlockService.latest_block()

    return utils.response(
        {
            "time": int(block.created.timestamp()),
            "blockhash": block.blockhash,
            "height": block.height,
            "chainwork": block.chainwork,
            "reward": float(block.reward),
        }
    )


@db.route("/transactions", defaults={"token": None}, methods=["GET"])
@db.route("/transactions/<path:token>", methods=["GET"])
@use_args(page_args, location="query")
@orm.db_session
def transactions(args, token):
    if not token:
        token = "PLB"

    transactions = TransactionIndex.select(
        lambda t: t.currency == token
    ).order_by(orm.desc(TransactionIndex.id))

    result = []

    pagination = {
        "total": math.ceil(transactions.count(distinct=False) / args["size"]),
        "page": args["page"],
    }

    transactions = transactions.page(args["page"], pagesize=args["size"])

    for index in transactions:
        transaction = index.transaction
        result.append(
            {
                "height": transaction.height,
                "blockhash": (
                    transaction.block.blockhash if transaction.block else None
                ),
                "timestamp": int(transaction.created.timestamp()),
                "confirmations": transaction.confirmations,
                "coinstake": transaction.coinstake,
                "coinbase": transaction.coinbase,
                "txhash": transaction.txid,
                "amount": float(index.amount),
            }
        )

    return utils.response(result, pagination=pagination)


@db.route("/blocks", methods=["GET"])
@use_args(page_args, location="query")
@orm.db_session
def blocks(args):
    blocks = BlockService.blocks()

    pagination = {
        "total": math.ceil(blocks.count(distinct=False) / args["size"]),
        "page": args["page"],
    }

    blocks = blocks.page(args["page"], pagesize=args["size"])

    result = []

    for block in blocks:
        result.append(
            {
                "height": block.height,
                "blockhash": block.blockhash,
                "timestamp": int(block.created.timestamp()),
                "reward": float(block.reward),
                "tx": len(block.transactions),
                "size": block.size,
            }
        )

    return utils.response(result, pagination=pagination)


@db.route("/height/<int:height>", methods=["GET"])
@orm.db_session
def height(height):
    block = BlockService.get_by_height(height)

    if block:
        return utils.response(
            {
                "reward": float(block.reward),
                "signature": block.signature,
                "blockhash": block.blockhash,
                "height": block.height,
                "tx": len(block.transactions),
                "timestamp": int(block.created.timestamp()),
                "merkleroot": block.merkleroot,
                "chainwork": block.chainwork,
                "version": block.version,
                "weight": block.weight,
                "stake": block.stake,
                "nonce": block.nonce,
                "size": block.size,
                "bits": block.bits,
            }
        )

    return utils.dead_response("Block not found"), 404


@db.route("/block/<string:bhash>", methods=["GET"])
@orm.db_session
def block(bhash):
    block = BlockService.get_by_hash(bhash)

    if block:
        return utils.response(
            {
                "reward": float(block.reward),
                "signature": block.signature,
                "blockhash": block.blockhash,
                "height": block.height,
                "tx": len(block.transactions),
                "timestamp": int(block.created.timestamp()),
                "merkleroot": block.merkleroot,
                "chainwork": block.chainwork,
                "version": block.version,
                "weight": block.weight,
                "stake": block.stake,
                "nonce": block.nonce,
                "size": block.size,
                "bits": block.bits,
            }
        )

    return utils.dead_response("Block not found"), 404


@db.route("/block/<string:bhash>/transactions", methods=["GET"])
@use_args(page_args, location="query")
@orm.db_session
def block_transactions(args, bhash):
    block = BlockService.get_by_hash(bhash)

    if block:
        transactions = Transaction.select(lambda t: t.block == block).order_by(
            Transaction.created
        )
        result = []

        pagination = {
            "total": math.ceil(
                transactions.count(distinct=False) / args["size"]
            ),
            "page": args["page"],
        }

        transactions = transactions.page(args["page"], pagesize=args["size"])

        for transaction in transactions:
            result.append(transaction.display())

        return utils.response(result, pagination=pagination)

    return utils.dead_response("Block not found"), 404


@db.route("/transaction/<string:txid>", methods=["GET"])
@orm.db_session
def transaction(txid):
    transaction = TransactionService.get_by_txid(txid)

    if transaction:
        return utils.response(transaction.display())

    data = NodeTransaction.info(txid)
    if not data["error"]:
        result = display.tx_to_db(data)
        return utils.response(result)

    return utils.dead_response("Transaction not found"), 404


@db.route("/history/<string:address>", methods=["GET"])
@use_args(page_args, location="query")
@orm.db_session
def history(args, address):
    address = AddressService.get_by_address(address)
    result = []

    pagination = {"total": 1, "page": 1}

    if address:
        transactions = address.transactions.order_by(orm.desc(Transaction.id))

        pagination = {
            "total": math.ceil(
                transactions.count(distinct=False) / args["size"]
            ),
            "page": args["page"],
        }

        transactions = transactions.page(args["page"], pagesize=args["size"])

        for transaction in transactions:
            result.append(transaction.display())

    return utils.response(result, pagination=pagination)


@db.route("/stats/<string:address>", methods=["GET"])
@orm.db_session
def count(address):
    address = AddressService.get_by_address(address)
    transactions = 0
    tokens = 0

    if address:
        transactions = len(address.transactions)
        for balance in address.balances:
            if balance.currency != "PLB" and balance.balance > 0:
                tokens += 1

    return utils.response({"transactions": transactions, "tokens": tokens})


@db.route("/richlist", defaults={"name": None}, methods=["GET"])
@db.route("/richlist/<path:name>", methods=["GET"])
@use_args(page_args_richlist, location="query")
@orm.db_session
def richlist(args, name):
    if not name:
        name = "PLB"

    balances = Balance.select(
        lambda b: b.currency == name and b.balance > 0
    ).order_by(orm.desc(Balance.balance))

    pagination = {
        "total": math.ceil(balances.count(distinct=False) / args["size"]),
        "page": args["page"],
    }

    balances = balances.page(args["page"], pagesize=args["size"])

    block = BlockService.latest_block()
    supply = 0

    if name == "PLB":
        supply = Decimal(utils.amount(utils.supply(block.height)["supply"]))

    else:
        if token := Token.get(name=name):
            supply = token.amount

    result = []

    for balance in balances:
        percantage = 0
        if balance.balance > 0:
            percantage = round(float((balance.balance / supply) * 100), 4)

        result.append(
            {
                "address": balance.address.address,
                "balance": float(balance.balance),
                "percentage": percantage,
            }
        )

    return utils.response(result, pagination=pagination)


@db.route("/richlist/full", defaults={"name": None}, methods=["GET"])
@db.route("/richlist/<string:name>/full", methods=["GET"])
@use_args(page_args, location="query")
@orm.db_session
def richlist_full(args, name):
    if not name:
        name = "PLB"

    balances = Balance.select(
        lambda b: b.currency == name and b.balance > 0
    ).order_by(orm.desc(Balance.balance))

    pagination = {
        "total": math.ceil(balances.count(distinct=False) / args["size"]),
        "page": args["page"],
    }

    block = BlockService.latest_block()
    supply = 0

    if name == "PLB":
        supply = Decimal(utils.amount(utils.supply(block.height)["supply"]))

    else:
        if token := Token.get(name=name):
            supply = token.amount

    result = []

    for balance in balances:
        percantage = 0
        if balance.balance > 0:
            percantage = round(float((balance.balance / supply) * 100), 4)

        result.append(
            {
                "address": balance.address.address,
                "balance": float(balance.balance),
                "percentage": percantage,
            }
        )

    return utils.response(result, pagination=pagination)


@db.route("/chart", methods=["GET"])
@orm.db_session
def chart():
    data = BlockService.chart()
    result = {}

    for entry in data:
        result[entry[0]] = entry[1]

    return utils.response(result)


@db.route("/balance/<string:address>", methods=["GET"])
@orm.db_session
def balance(address):
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

            if balance.balance == 0 and balance.currency != "PLB":
                continue

            result.append(
                {
                    "currency": balance.currency,
                    "balance": float(unspent),
                    "locked": float(locked),
                }
            )

    return utils.response(result)


@db.route("/address/<string:address>", methods=["GET"])
@orm.db_session
def address(address):
    address = AddressService.get_by_address(address)
    block = BlockService.latest_block()
    balances = []

    result = {"balances": [], "transactions": 0, "tokens": 0}

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

            if balance.balance == 0 and balance.currency != "PLB":
                continue

            if balance.currency != "PLB":
                result["tokens"] += 1

            balances.append(
                {
                    "currency": balance.currency,
                    "balance": float(unspent),
                    "locked": float(locked),
                }
            )

        result["transactions"] = len(address.transactions)
        result["balances"] = balances

    return utils.response(result)


@db.route("/address/<string:address>/transactions", methods=["GET"])
@use_args(page_args, location="query")
@orm.db_session
def address_transactions(args, address):
    address = AddressService.get_by_address(address)

    if address:
        result = []

        transactions = address.transactions.order_by(
            orm.desc(Transaction.created)
        )

        pagination = {
            "total": math.ceil(
                transactions.count(distinct=False) / args["size"]
            ),
            "page": args["page"],
        }

        transactions = transactions.page(args["page"], pagesize=args["size"])

        for transaction in transactions:
            result.append(transaction.display())

        return utils.response(result, pagination=pagination)

    return utils.dead_response("Block not found"), 404


@db.route("/mempool", methods=["GET"])
@orm.db_session
def mempool():
    data = NodeGeneral.mempool()

    if not data["error"]:
        mempool = data["result"]["tx"]
        new = []

        for txid in mempool:
            tx = NodeTransaction.info(txid)
            new.append(display.tx_to_db(tx))

        data["result"]["tx"] = new

    return data


@db.route("/token/<path:name>", methods=["GET"])
@orm.db_session
def token_data(name):
    token = Token.get(name=name)

    if token:
        holders = Balance.select(
            lambda b: b.balance > 0 and b.currency == name
        ).count(distinct=False)

        return utils.response(
            {
                "logo": utils.get_logo(token.name),
                "amount": float(token.amount),
                "reissuable": token.reissuable,
                "category": token.category,
                "height": token.height,
                "block": token.block,
                "units": token.units,
                "name": token.name,
                "ipfs": token.ipfs,
                "holders": holders,
            }
        )

    return utils.dead_response("Token not found"), 404


@db.route("/broadcast", methods=["POST"])
@use_args(broadcast_args, location="json")
def broadcast(args):
    return NodeTransaction.broadcast(args["raw"])


@db.route("/tokens", methods=["GET"])
@use_args(tokens_args, location="query")
@orm.db_session
def tokens(args):
    tokens = Token.select(lambda t: t.category in ["sub", "root"])

    # Hide test tokens from tokens list (WIP)
    tokens = tokens.filter(lambda t: not t.name.startswith("TEST"))
    tokens = tokens.filter(lambda t: not t.name.startswith("DEV"))

    if args["search"]:
        tokens = tokens.filter(lambda t: t.name.startswith(args["search"]))

    pagination = {
        "total": math.ceil(tokens.count(distinct=False) / args["size"]),
        "page": args["page"],
    }

    tokens = tokens.page(args["page"], 100)

    result = []

    for token in tokens:
        result.append(token.display)

    return utils.response(result, pagination=pagination)


@db.route("/tokens/list", methods=["GET"])
@use_args(tokens_args, location="query")
@orm.db_session
def tokens_list(args):
    tokens = Token.select(lambda t: t.category in ["sub", "root"])

    if args["search"]:
        tokens = tokens.filter(lambda t: t.name.startswith(args["search"]))

    pagination = {
        "total": math.ceil(tokens.count(distinct=False) / args["size"]),
        "page": args["page"],
    }

    tokens = tokens.page(args["page"], 100)

    result = []

    for token in tokens:
        result.append(token.name)

    return utils.response(result, pagination=pagination)


@db.route("/stats/general", methods=["GET"])
@orm.db_session
def general_stats():
    return utils.response(
        {
            "addresses": 75419,
            "transactions": 123456,
            "tokens": 12,
            "nodes": 300,
            "change": {
                "addresses": 510,
                "transactions": 650,
                "tokens": 3,
                "nodes": -10,
            },
        }
    )


@db.route("/stats/price", methods=["GET"])
@orm.db_session
def price_stats():
    return utils.response(
        {
            "price": 1.263,
            "marketcap": 6546042.20,
            "volume": 2093010.05,
            "change": {
                "price": 31.9,
                "marketcap": 25.1,
                "volume": -10.3,
            },
        }
    )


@db.route("/chart/price", methods=["GET"])
@orm.db_session
def price_chart():
    result = [
        {"timestamp": 1644789600, "value": 5.86},
        {"timestamp": 1644876000, "value": 1.7},
        {"timestamp": 1644962400, "value": 7.98},
        {"timestamp": 1645048800, "value": 4.63},
        {"timestamp": 1645135200, "value": 9.82},
        {"timestamp": 1645221600, "value": 4.82},
        {"timestamp": 1645308000, "value": 3.86},
        {"timestamp": 1645394400, "value": 1.93},
        {"timestamp": 1645480800, "value": 4.06},
        {"timestamp": 1645567200, "value": 7.08},
        {"timestamp": 1645653600, "value": 4.77},
        {"timestamp": 1645740000, "value": 8.15},
        {"timestamp": 1645826400, "value": 9.94},
        {"timestamp": 1645912800, "value": 9.95},
        {"timestamp": 1645999200, "value": 2.96},
        {"timestamp": 1646085600, "value": 8.38},
        {"timestamp": 1646172000, "value": 4.66},
        {"timestamp": 1646258400, "value": 8.12},
        {"timestamp": 1646344800, "value": 3.15},
        {"timestamp": 1646431200, "value": 7.52},
        {"timestamp": 1646517600, "value": 3.29},
        {"timestamp": 1646604000, "value": 6.36},
        {"timestamp": 1646690400, "value": 8.77},
        {"timestamp": 1646776800, "value": 8.11},
        {"timestamp": 1646863200, "value": 2.97},
        {"timestamp": 1646949600, "value": 6.06},
        {"timestamp": 1647036000, "value": 4.36},
        {"timestamp": 1647122400, "value": 8.35},
        {"timestamp": 1647208800, "value": 5.13},
    ]

    return utils.response(result)


@db.route("/chart/transactions", methods=["GET"])
@use_args(chart_args, location="query")
@orm.db_session
def transactions_chart(args):
    result = [
        {"timestamp": 1644789600, "value": 894},
        {"timestamp": 1644876000, "value": 1122},
        {"timestamp": 1644962400, "value": 108},
        {"timestamp": 1645048800, "value": 499},
        {"timestamp": 1645135200, "value": 1435},
        {"timestamp": 1645221600, "value": 915},
        {"timestamp": 1645308000, "value": 1101},
        {"timestamp": 1645394400, "value": 1017},
        {"timestamp": 1645480800, "value": 620},
        {"timestamp": 1645567200, "value": 1147},
        {"timestamp": 1645653600, "value": 479},
        {"timestamp": 1645740000, "value": 462},
        {"timestamp": 1645826400, "value": 577},
        {"timestamp": 1645912800, "value": 384},
        {"timestamp": 1645999200, "value": 346},
        {"timestamp": 1646085600, "value": 467},
        {"timestamp": 1646172000, "value": 1220},
        {"timestamp": 1646258400, "value": 1027},
        {"timestamp": 1646344800, "value": 510},
        {"timestamp": 1646431200, "value": 174},
        {"timestamp": 1646517600, "value": 225},
        {"timestamp": 1646604000, "value": 1220},
        {"timestamp": 1646690400, "value": 289},
        {"timestamp": 1646776800, "value": 103},
        {"timestamp": 1646863200, "value": 515},
        {"timestamp": 1646949600, "value": 1053},
        {"timestamp": 1647036000, "value": 1317},
        {"timestamp": 1647122400, "value": 416},
        {"timestamp": 1647208800, "value": 799},
    ]

    return utils.response(result)


@db.route("/chart/addresses", methods=["GET"])
@use_args(chart_args, location="query")
@orm.db_session
def addresses_chart(args):
    result = [
        {"timestamp": 1644789600, "value": 500},
        {"timestamp": 1644876000, "value": 1478},
        {"timestamp": 1644962400, "value": 671},
        {"timestamp": 1645048800, "value": 774},
        {"timestamp": 1645135200, "value": 109},
        {"timestamp": 1645221600, "value": 1437},
        {"timestamp": 1645308000, "value": 715},
        {"timestamp": 1645394400, "value": 1351},
        {"timestamp": 1645480800, "value": 500},
        {"timestamp": 1645567200, "value": 575},
        {"timestamp": 1645653600, "value": 1417},
        {"timestamp": 1645740000, "value": 1485},
        {"timestamp": 1645826400, "value": 294},
        {"timestamp": 1645912800, "value": 1001},
        {"timestamp": 1645999200, "value": 1042},
        {"timestamp": 1646085600, "value": 640},
        {"timestamp": 1646172000, "value": 910},
        {"timestamp": 1646258400, "value": 607},
        {"timestamp": 1646344800, "value": 1208},
        {"timestamp": 1646431200, "value": 390},
        {"timestamp": 1646517600, "value": 728},
        {"timestamp": 1646604000, "value": 856},
        {"timestamp": 1646690400, "value": 151},
        {"timestamp": 1646776800, "value": 1043},
        {"timestamp": 1646863200, "value": 475},
        {"timestamp": 1646949600, "value": 951},
        {"timestamp": 1647036000, "value": 185},
        {"timestamp": 1647122400, "value": 927},
        {"timestamp": 1647208800, "value": 359},
    ]

    return utils.response(result)
