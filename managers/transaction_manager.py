'''
* Transaction Manager never fails
* SDM tracks the up/down of its site, and TM contains all SDMs
'''
import math
from managers.data_manager import SiteDataManager
from constants import READ, RECOVER, WRITE, FAIL, BEGIN, BEGIN_RO, DUMP, END, DeadlockResult
from collections import defaultdict


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

    def get_start_time(self):
        return self.transaction_start_time

    def should_abort(self):
        # Tells whether a transaction will abort or not
        return self.abort

    def abort_transaction(self):
        # Aborts a transaction
        self.abort = True

    def get_sites_touched(self):
        return self.transaction_accessed

    def add_touched_site(self, site_id):
        self.transaction_accessed.append(site_id)


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

    def print_event_queue(self):
        print(self.event_queue)

    def print_transaction_db(self):
        print(self.transaction_db)

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
            print(f"Transaction {obj.transaction} [Read Only] starts")

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

    def read(self, obj):

        # Read operation for normal reads.
        # Read object attributes below
        # self.data_item = variable
        # self.transaction_name = transaction

        # Check if transaction is valid :
        if obj.transaction_name not in self.transaction_db:
            raise Exception(f"Invalid Transaction {obj.transaction_name}")

        # This can be optimised - we dont have to check all sites for the variable - some variable are only in
        # certain sites
        for SDM in self.SDMs.values():
            if SDM.site_status() and SDM.check_membership(obj.data_item):

                # Read from SDM :
                # response is a namedtuple with fields [success, value]
                response = SDM.read(obj.transaction_name, obj.data_item)
                if response.success:

                    # Track that this transaction touched this site.
                    self.transaction_db[obj.transaction_name].add_touched_site(SDM.site_number)
                    print(f"{obj.transaction_name} reads {obj.data_item}.{SDM.site_number} : {response.value}")
                    return True

        # Cant find variable at any site or site containing variable is down
        return False

    def read_from_snapshot(self, obj):

        # Read operation for Read Only transaction Reads.
        # Read object attributes below
        # self.data_item = variable
        # self.transaction_name = transaction

        # Check if transaction is valid :
        if obj.transaction_name not in self.transaction_db:
            raise Exception(f"Invalid Transaction {obj.transaction_name}")

        read_only_transaction_start_time = self.transaction_db[obj.transaction_name].get_start_time()

        for SDM in self.SDMs.values():
            if SDM.site_status() and SDM.check_membership(obj.data_item):

                # Read from SDM :
                # response is a namedtuple with fields [success, value]
                # Pass the start time of the transaction to SDM
                response = SDM.read_snapshot(obj.data_item, read_only_transaction_start_time)
                if response.success:
                    print(f"{obj.transaction_name} [Read-Only] reads {obj.data_item}.{SDM.site_number} : {response.value}")
                    return True

        # Cant find variable at any site or site containing variable is down
        return False

    def write(self, obj):

        # Write operation for Write transaction. Write object attributes below
        # self.data_item = variable
        # self.transaction_name = transaction
        # self.new_value = new_value

        # Check if transaction is valid.
        if obj.transaction_name not in self.transaction_db:
            raise Exception(f"Invalid Transaction {obj.transaction_name}")

        write_site_available, got_all_locks = False, True
        written_sites = []

        for SDM in self.SDMs.values():
            if SDM.site_status() and SDM.check_membership(obj.data_item):
                write_site_available = True
                response = SDM.test_write_lock(obj.transaction_name, obj.data_item)

                if not response:
                    # Could not get one or many required w-locks
                    got_all_locks = False

        if write_site_available and got_all_locks:
            # If we have write site(s) available, and we have locks to all the relevant data items, proceed

            for SDM in self.SDMs.values():
                if SDM.site_status() and SDM.check_membership(obj.data_item):

                    # Perform Write
                    SDM.write(obj.transaction_name, obj.data_item, obj.new_value)

                    # Track that this transaction touched this site.
                    self.transaction_db[obj.transaction_name].add_touched_site(SDM.site_number)
                    written_sites.append(SDM.site_number)

            print(f"{obj.transaction_name} writes {obj.data_item}:{obj.new_value} to - {written_sites}")
            return True

        # Write failed.
        return False

    def end(self, obj):
        # Transaction will either commit, or abort when end() is called.
        # The End_IO class object is passed : self.transaction = transaction

        # Check if transaction is valid.
        if obj.transaction not in self.transaction_db:
            raise Exception(f"Invalid Transaction {obj.transaction}")

        # Check if it should abort :
        if self.transaction_db[obj.transaction].should_abort():

            # Transaction Aborts - this abort is due to site failure
            # 1. Tell all SDMs to abort this transaction
            for SDM in self.SDMs.values():
                SDM.abort(obj.transaction)

            # 2. Remove this transaction from transaction_db
            del self.transaction_db[obj.transaction]

            print(f"Transaction {obj.transaction} aborts: Site Failure")

        else:

            # Transaction can commit.
            # 1. Tell all SDMs to commit this transaction
            for SDM in self.SDMs.values():
                SDM.commit(obj.transaction, self.GLOBAL_TIME)

            # 2. Remove the transaction from the transaction_db
            del self.transaction_db[obj.transaction]

            print(f"Transaction {obj.transaction} commits")

    def fail(self, obj):

        # Site fails. Site_IO input object sent here:
        # self.site = site
        SDM = self.SDMs[obj.site]

        # Check if the site is already down:
        if not SDM.site_status():
            raise Exception(f"Site {obj.site} is already down.")

        # 1. Fail site
        SDM.fail(self.GLOBAL_TIME)

        # 2. Identify the transactions that will abort because the site went down, and abort those Ts
        for transaction in self.transaction_db.values():
            # Doesn't apply to RO
            if transaction.check_read_only():
                continue

            sites_touched = transaction.get_sites_touched()
            if not transaction.should_abort() and obj.site in sites_touched:
                # This transaction will abort
                transaction.abort_transaction()

        print(f"Site {obj.site} fails")

    def recover(self, obj):
        # Site recovers
        # Recover_IO used here has : self.site = site

        SDM = self.SDMs[obj.site]
        if SDM.site_status():
            raise Exception(f"Site {obj.site} is still up")

        SDM.recover(self.GLOBAL_TIME)
        print(f"Site {obj.site} recovers")

    def dump(self):
        for SDM in self.SDMs.values():
            print(SDM.site_dump())

    def generate_tm_waits_graph(self):
        # Combine the waits-for graphs from all sites into one
        tm_waits_graph = defaultdict(set)
        for SDM in self.SDMs.values():
            if SDM.site_status():
                wait_graph = SDM.return_waits_for_graph()
                for start, end_set in wait_graph.items():
                    # Add all edges into full waits-graph
                    tm_waits_graph[start].update(end_set)

        return tm_waits_graph

    def abort_deadlocked_transaction(self, transaction_name):
        '''
        * A deadlock has occured and this transaction name has been picked to kill
        '''

        # Abort this transaction at all sites.
        for SDM in self.SDMs.values():
            SDM.abort(transaction_name)

        # Remove transaction from transaction_db
        del self.transaction_db[transaction_name]
        print(f"Transaction {transaction_name} aborted to resolve deadlock")

    def deadlock_graph_check(self, tm_waits_graph):
        '''
        * Scans the waits-graph for deadlocks and returns the youngest transaction name if
        there is one
        * Return value is namedtuple type: DeadlockResult(is_deadlock:True , transaction_name:"x3")
        * Iterative DFS used for deadlock detection
        '''

        youngest_transaction = None
        youngest_transaction_time = -math.inf

        # If there's no waits graph, it wont enter the next loop, the youngest_tran == None and returns false
        for start_node in list(tm_waits_graph.keys()):
            visited = set()
            deadlock_flag = False
            stack = [start_node]
            while stack:
                node = stack.pop()
                visited.add(node)
                for nei in tm_waits_graph[node]:
                    if nei == start_node:
                        deadlock_flag = True
                        break
                    elif nei not in visited and nei in tm_waits_graph.keys():
                        stack.append(nei)

                if deadlock_flag:
                    break

            if deadlock_flag and self.transaction_db[start_node].transaction_start_time > youngest_transaction_time:
                youngest_transaction = start_node
                youngest_transaction_time = self.transaction_db[start_node].transaction_start_time

        if youngest_transaction:
            return DeadlockResult(True, youngest_transaction)
        else:
            return DeadlockResult(False, None)

    def test_for_deadlock(self):
        '''
        * Combines the waits-graph from all sites into 1 graph.
        * Checks this graph for deadlocks.
        * If a deadlock is found, the youngest transaction is aborted.
        * returns True if it finds a deadlock.
        '''

        tm_waits_graph = self.generate_tm_waits_graph()
        test_result = self.deadlock_graph_check(tm_waits_graph)
        if not test_result.is_deadlock:
            return False
        else:
            # Deadlock detected.
            print("# Deadlock Detected #")
            self.abort_deadlocked_transaction(test_result.transaction_name)
            return True

    def process_event_queue(self):
        '''
        The event-queue consists of queued read(only) and write requests.
        '''

        for event in list(self.event_queue):
            operation, obj = event
            if obj.transaction_name not in self.transaction_db:
                self.event_queue.remove(event)
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
                self.dump()
            else:
                raise Exception("Invalid Operation")

            self.process_event_queue()
            self.GLOBAL_TIME += 1
