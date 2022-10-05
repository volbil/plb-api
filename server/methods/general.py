from server import utils

class General():
    @classmethod
    def info(cls):
        data = utils.make_request("getblockchaininfo")

        if data["error"] is None:
            data["result"]["mempool"] = 0
            data["result"]["reward"] = utils.reward(data["result"]["blocks"])
            data["result"].pop("verificationprogress")
            data["result"].pop("pruned")
            data["result"].pop("softforks")
            data["result"].pop("bip9_softforks")
            data["result"].pop("warnings")
            data["result"].pop("size_on_disk")

            mempool = cls.mempool()
            if mempool["error"] is None:
                data["result"]["mempool"] = mempool["result"]["size"]

            nethash = utils.make_request("getnetworkhashps", [120, data["result"]["blocks"]])
            if nethash["error"] is None:
                data["result"]["nethash"] = int(nethash["result"])

        return data

    @classmethod
    def supply(cls):
        data = utils.make_request("getblockchaininfo")
        height = data["result"]["blocks"]
        result = utils.supply(height)
        result["height"] = height

        return result

    @classmethod
    def fee(cls):
        # data = utils.make_request("estimatesmartfee", [6])

        # if data["error"] is None:
        #     data["result"]["feerate"] = utils.satoshis(data["result"]["feerate"])
        # else:
        #     data = utils.response({
        #         "feerate": utils.satoshis(0.001),
        #         "blocks": 6
        #     })

        # return data

        return utils.response({
            "feerate": utils.satoshis(0.01),
            "blocks": 6
        })

    @classmethod
    def mempool(cls):
        data = utils.make_request("getmempoolinfo")

        if data["error"] is None:
            if data["result"]["size"] > 0:
                mempool = utils.make_request("getrawmempool")["result"]
                data["result"]["tx"] = mempool
            else:
                data["result"]["tx"] = []

        return data

    @classmethod
    def current_height(cls):
        data = utils.make_request("getblockcount")
        height = 0

        if data["error"] is None:
            height = data["result"]

        return height
