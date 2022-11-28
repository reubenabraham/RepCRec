'''
* Transaction Manager never fails
* SDM tracks the up/down of its site, and TM contains all SDMs
* If the TM requests a read on a replicated data item x for read-write transaction T and cannot get it due to failure,
the TM should try another site (all in the same step). If no relevant site is available, then T must wait.
* As mentioned above, if every site failed after a commit to x but before T began, then the read-only transaction should abort.

'''
from data_manager import SiteDataManager


class Transaction:
    def __init__(self, transaction_name, transaction_start_time):
        self.transaction_name = transaction_name
        self.transaction_start_time = transaction_start_time
        self.read_only = False
        self.transaction_accessed = list()
        self.abort = False

    def __repr__(self):
        return f"Transaction Name: {self.transaction_name} ; Transaction Start: {self.transaction_start_time} ; Transaction R-O: {1 if self.read_only else 0}"

    def set_read_only(self):
        self.read_only = True

    def get_sites_touched(self):
        return self.transaction_accessed


class Read:
    def __init__(self, variable: str, transaction: str):
        self.data_item = variable
        self.transaction_name = transaction

    def __repr__(self):
        return "R("+self.transaction_name+", "+self.data_item+")"


class Write:

    def __init__(self, variable: str, transaction: str, new_value: str):
        self.data_item = variable
        self.transaction_name = transaction
        self.new_value = new_value

    def __repr__(self):
        return "W(" + self.transaction_name + ", " + self.data_item + ", " + self.new_value + ")"


class TransactionManager:
    '''
    Contains all 10 SiteDataManagers
    '''
    def __init__(self):

        self.SDMs = dict()
        for i in range(1, 11):
            self.SDMs[str(i)] = SiteDataManager(str(i))




