from ..services import TokenService
from .. import utils

# ToDo: Get rid of all this

def token_to_db(data):
    result = data["result"]

    return {
        "reissuable": True if result["reissuable"] == 1 else False,
        "amount": result["amount"],
        "units": result["units"],
        "name": result["name"],
        "total": None
    }

def tx_to_db(data):
    result = data["result"]

    output_amount = 0
    input_amount = 0
    outputs = []
    inputs = []

    for vin in data["result"]["vin"]:
        if "coinbase" in vin:
            continue

        amount = utils.amount(vin["value"])
        currency = "PLB"

        if "token" in vin["scriptPubKey"]:
            currency = vin["scriptPubKey"]["token"]["name"]
            amount = vin["scriptPubKey"]["token"]["amount"]

        address = vin["scriptPubKey"]["addresses"][0]

        inputs.append({
            "address": address,
            "currency": currency,
            "amount": amount
        })

        if currency == "PLB":
            input_amount += amount

    for vout in data["result"]["vout"]:
        if vout["scriptPubKey"]["type"] in ["nonstandard", "nulldata"]:
            continue

        category = vout["scriptPubKey"]["type"]
        amount = utils.amount(vout["value"])
        currency = "PLB"
        timelock = 0

        if "token" in vout["scriptPubKey"]:
            timelock = vout["scriptPubKey"]["token"]["token_lock_time"]
            currency = vout["scriptPubKey"]["token"]["name"]
            amount = vout["scriptPubKey"]["token"]["amount"]

        if "timelock" in vout["scriptPubKey"]:
            timelock = vout["scriptPubKey"]["timelock"]

        address = vout["scriptPubKey"]["addresses"][0]

        outputs.append({
            "address": address,
            "currency": currency,
            "timelock": timelock,
            "amount": amount,
            "category": category,
            "spent": False
        })

        if currency == "PLB":
            output_amount += amount

    confirmations = result["confirmations"] if "confirmations" in result else 0

    return {
        "confirmations": confirmations,
        "fee": float(input_amount - output_amount),
        "timestamp": result["timestamp"],
        "amount": utils.amount(result["amount"]),
        "coinstake": False,
        "height": data["result"]["height"],
        "coinbase": False,
        "txid": result["txid"],
        "size": result["size"],
        "outputs": outputs,
        "mempool": True if result["height"] < 0 else False,
        "inputs": inputs
    }

def tx_to_wallet(data):
    result = data["result"]

    output_amount = 0
    input_amount = 0
    outputs = []
    inputs = []

    for vin in data["result"]["vin"]:
        if "coinbase" in vin:
            continue

        amount = vin["value"]
        currency = "PLB"

        if "token" in vin["scriptPubKey"]:
            currency = vin["scriptPubKey"]["token"]["name"]
            amount = utils.satoshis(vin["scriptPubKey"]["token"]["amount"])

        address = vin["scriptPubKey"]["addresses"][0]
        units = TokenService.get_units(currency)

        inputs.append({
            "address": address,
            "currency": currency,
            "amount": amount,
            "units": units
        })

        if currency == "PLB":
            input_amount += amount

    for vout in data["result"]["vout"]:
        if vout["scriptPubKey"]["type"] in ["nonstandard", "nulldata"]:
            continue

        category = vout["scriptPubKey"]["type"]
        amount = vout["value"]
        currency = "PLB"
        timelock = 0

        if "token" in vout["scriptPubKey"]:
            timelock = vout["scriptPubKey"]["token"]["token_lock_time"]
            currency = vout["scriptPubKey"]["token"]["name"]
            amount = utils.satoshis(vout["scriptPubKey"]["token"]["amount"])

        if "timelock" in vout["scriptPubKey"]:
            timelock = vout["scriptPubKey"]["timelock"]

        address = vout["scriptPubKey"]["addresses"][0]
        units = TokenService.get_units(currency)

        outputs.append({
            "address": address,
            "currency": currency,
            "timelock": timelock,
            "amount": amount,
            "category": category,
            "units": units,
            "spent": False
        })

        if currency == "PLB":
            output_amount += amount

    confirmations = result["confirmations"] if "confirmations" in result else 0

    return {
        "confirmations": confirmations,
        "fee": float(input_amount - output_amount),
        "timestamp": result["timestamp"],
        "amount": result["amount"],
        "coinstake": False,
        "height": data["result"]["height"],
        "coinbase": False,
        "txid": result["txid"],
        "size": result["size"],
        "outputs": outputs,
        "mempool": True if result["height"] < 0 else False,
        "inputs": inputs
    }
