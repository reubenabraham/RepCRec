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

    def check_read_only(self):
        if self.read_only:
            return True
        else:
            return False


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
    Contains
    - all 10 SiteDataManagers
    - all transaction objects
    - event queue - which contains queued Reads and Writes
    '''
    def __init__(self):

        # dict that contains all SDMs
        self.SDMs = dict()

        # transaction_db stores the Transaction objects
        self.transaction_db = dict()

        # Event queue consists of queued Reads and Writes from transactions
        self.event_queue = list()

        for i in range(1, 11):
            sdm_obj = SiteDataManager(str(i))
            self.SDMs[str(i)] = sdm_obj

        # set global time=0
        self.GLOBAL_TIME = 0

    def test_for_deadlock(self):
        return True

    def process_event_queue(self):

        for event in self.event_queue:
            operation, obj = event

            # If the transaction is not in the transaction_db, then remove it
            # clean this up. remove this either when the transaction completes or when it aborts
            if obj.transaction_name not in self.transaction_db:
                self.event_queue.remove(event)
                print("Clean this up- should be removed elsewhere")
            else:

                operation_status = False
                if operation == READ:

                    # Check if read only or regular read
                    if self.transaction_db[obj.transaction_name].check_read_only():
                        # obj is instance of Read class
                        operation_status = self.read_from_snapshot(obj)
                    else:
                        # obj is instance of Read class
                        operation_status = self.read(obj)

                elif operation == WRITE:
                    # obj here is an instance of Write
                    operation_status = self.write(obj)

                else:
                    raise Exception("op should be read/write - we should not hit this code path.")

                if operation_status:
                    # If the operation was successful then remove the event from the queue
                    self.event_queue.remove(event)

    def read(self, obj):
        return True

    def write(self, obj):
        return True

    def read_from_snapshot(self, obj):
        return True

    def print_event_queue(self):
        print(self.event_queue)

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
                self.queue_read(obj)
            elif operation == WRITE:
                self.queue_write(obj)
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

    def queue_read(self, obj):

        # Check if the transaction is valid
        if obj.transaction not in self.transaction_db:
            raise Exception(f"Invalid Transaction {obj.transaction}")

        # Queue the Read operation
        read_obj = Read(obj.variable, obj.transaction)
        self.event_queue.append((READ, read_obj))

    def queue_write(self, obj):

        # Check if the transaction is valid
        if obj.transaction not in self.transaction_db:
            raise Exception(f"Invalid Transaction {obj.transaction}")

        write_obj = Write(obj.variable, obj.transaction, obj.new_value)
        self.event_queue.append((WRITE, write_obj))

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




