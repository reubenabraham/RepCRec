'''
* Transaction Manager never fails
* SDM tracks the up/down of its site, and TM contains all SDMs
* If the TM requests a read on a replicated data item x for read-write transaction T and cannot get it due to failure,
the TM should try another site (all in the same step). If no relevant site is available, then T must wait.
* As mentioned above, if every site failed after a commit to x but before T began, then the read-only transaction should abort.

'''
from data_manager import SiteDataManager
from constants import READ, RECOVER, WRITE, FAIL, BEGIN, BEGIN_RO, DUMP, END


class Transaction:
    def __init__(self, transaction_name, transaction_start_time):
        self.transaction_name = transaction_name
        self.transaction_start_time = transaction_start_time
        self.read_only = False
        self.transaction_accessed = list()
        self.abort = False

    def __repr__(self):
        return f"Transaction Name: {self.transaction_name} ; Transaction Start: {self.transaction_start_time} ; Transaction R-O: {'YES' if self.read_only else 'NO'}"

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
        # transaction_db stores the Transaction objects
        self.transaction_db = dict()
        # Event queue consists of queued Reads and Writes from transactions
        self.event_queue = list()
        for i in range(1, 11):
            sdm_obj = SiteDataManager(str(i))
            self.SDMs[str(i)] = sdm_obj

        self.GLOBAL_TIME = 0

    def test_for_deadlock(self):
        return True

    def process_event_queue(self):
        pass

    def print_transaction_db(self):
        print(self.transaction_db)

    def simulation(self, instruction_queue):
        '''
        Processes each instruction from the instruction queue.
        This is the main simulation
        '''

        while instruction_queue:

            print(f"-------- time:{self.GLOBAL_TIME} --------")

            operation, obj = instruction_queue.popleft()

            # Check for deadlock at the start of the tick :
            if self.test_for_deadlock():
                self.process_event_queue()

            # operation, obj
            if operation == BEGIN:
                self.begin(obj)
            elif operation == BEGIN_RO:
                self.begin_ro(obj)
            elif operation == READ:
                self.read(obj)
            elif operation == WRITE:
                self.write(obj)
            elif operation == FAIL:
                self.fail(obj)
            elif operation == RECOVER:
                self.recover(obj)
            elif operation == END:
                self.end(obj)
            elif operation == DUMP:
                # self.dump() - this is working - just uncomment when needed
                pass
            else:
                raise Exception("Invalid Operation")

            self.process_event_queue()
            self.GLOBAL_TIME += 1

    def begin(self, obj):

        # Check if the transaction is already in the system
        if obj.transaction in self.transaction_db:
            raise Exception(f"Transaction {obj.transaction} already exists")
        else:
            # Create and start the transaction
            transaction_obj = Transaction(obj.transaction, self.GLOBAL_TIME)
            self.transaction_db[obj.transaction] = transaction_obj
            print(f"Transaction {obj.transaction} starts")

    def begin_ro(self, obj):

        # Check if the transaction is already in the system
        if obj.transaction in self.transaction_db:
            raise Exception(f"Transaction {obj.transaction} already exists")
        else:
            # Create and start the transaction
            transaction_obj = Transaction(obj.transaction, self.GLOBAL_TIME)
            transaction_obj.set_read_only()
            self.transaction_db[obj.transaction] = transaction_obj
            print(f"[Read Only] Transaction {obj.transaction} starts")

    def read(self, obj):
        pass

    def write(self, obj):
        pass

    def fail(self, obj):
        pass

    def dump(self):

        print(f"----- DUMP -----")
        for SDM in self.SDMs.values():
            print(SDM.site_dump())
        print(f"--- END DUMP ---")

    def end(self, obj):
        pass

    def recover(self, obj):
        pass




