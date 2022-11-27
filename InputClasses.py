class Read_IO:
    def __init__(self, transaction: str, variable: str):
        self.transaction = transaction
        self.variable = variable

    def __repr__(self):
        return "R("+self.transaction+","+self.variable+")"


class Write_IO:
    def __init__(self, transaction: str, variable: str, new_value: str):
        self.transaction = transaction
        self.variable = variable
        self.new_value = new_value

    def __repr__(self):
        return "W(" + self.transaction + "," + self.variable + "," + self.new_value + ")"


class Begin_IO:
    def __init__(self, transaction: str):
        self.transaction = transaction

    def __repr__(self):
        return "begin(" + self.transaction + ")"


class BeginRO_IO(Begin_IO):
    def __init__(self, transaction: str):
        Begin_IO.__init__(self, transaction)

    def __repr__(self):
        return "beginRO(" + self.transaction + ")"


class Fail_IO:
    def __init__(self, site: str):
        self.site = site

    def __repr__(self):
        return "fail(" + self.site + ")"


class Recover_IO:
    def __init__(self, site: str):
        self.site = site

    def __repr__(self):
        return "recover(" + self.site + ")"


class End_IO:
    def __init__(self, transaction: str):
        self.transaction = transaction

    def __repr__(self):
        return "end(" + self.transaction + ")"


class Dump_IO:
    def __repr__(self):
        return "dump"




