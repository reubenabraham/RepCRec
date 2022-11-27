class Read:
    def __init__(self, transaction: str, variable: str):
        self.transaction = transaction
        self.variable = variable

    def __repr__(self):
        return "R("+self.transaction+","+self.variable+")"


class Write:
    def __init__(self, transaction: str, variable: str, new_value: str):
        self.transaction = transaction
        self.variable = variable
        self.new_value = new_value

    def __repr__(self):
        return "W(" + self.transaction + "," + self.variable + "," + self.new_value + ")"


class Begin:
    def __init__(self, transaction: str):
        self.transaction = transaction

    def __repr__(self):
        return "begin(" + self.transaction + ")"


class BeginRO(Begin):
    def __init__(self, transaction: str):
        Begin.__init__(self, transaction)

    def __repr__(self):
        return "beginRO(" + self.transaction + ")"


class Fail:
    def __init__(self, site: str):
        self.site = site

    def __repr__(self):
        return "fail(" + self.site + ")"


class Recover:
    def __init__(self, site: str):
        self.site = site

    def __repr__(self):
        return "recover(" + self.site + ")"


class End:
    def __init__(self, transaction: str):
        self.transaction = transaction

    def __repr__(self):
        return "end(" + self.transaction + ")"


class Dump:
    def __repr__(self):
        return "dump"




