from .. import utils

class Token():
    @classmethod
    def data(cls, name: str):
        return utils.make_request("gettokendata", [name])

    @classmethod
    def list(cls, offset: int, count: int, search=""):
        if count > 200:
            count = 200

        data = utils.make_request("listtokens", [f"{search}*", True, count, offset])

        remove = []

        # ToDo: temporary solution, remove later
        for name in data["result"]:
            if name[0] == "@":
                remove.append(name)

            # Hide TEST tokens (WIP)
            if name.startswith("TEST"):
                remove.append(name)

        for name in remove:
            del data["result"][name]

        return data
