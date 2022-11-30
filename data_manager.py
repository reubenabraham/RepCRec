from constants import UP, DOWN, site_variables_init
from collections import namedtuple, defaultdict, deque
from constants import READ, WRITE
from lock_manager import ReadLock, WriteLock, QueueLock, LockManager

# ----- Move these named tuples to constants.py -----
# Named tuple use to return responses for Reads/Writes
Result = namedtuple('Result', 'success value')
DataItemCommitValue = namedtuple('DataItemCommitValue', 'value commit_timestamp')
DataItemTempValue = namedtuple('DataItemTempValue', 'value transaction_name')
OperationResult = namedtuple('OperationResult', 'success value')


class DataItem:
    '''
    Contains data item info like:
    - name
    - comitted value(s), temp value
    - replicated or not
    '''
    def __init__(self, name: str, commit_value_obj):
        self.name = name
        # Need to store all committed values because for RO transactions, we have to pick up commited
        # value at a certain time. Latest committed value at the left, and older ones after
        # the value variable is of DataItemCommitValue type
        self.committed_values = deque()
        self.committed_values.appendleft(commit_value_obj)
        # temp_value is of DataItemTempValue type
        self.temp_value = None
        self.replicated = False
        self.can_read = True

    def __repr__(self):
        return self.name+f"= {list(self.get_committed_value())}"

    def readable(self):
        # Determines if a data item is readable. Replicated variables cannot be read at
        # a site that was down and came back up.
        return self.can_read

    def is_replicated(self):
        return self.replicated

    def get_committed_value(self):
        # Gets presently committed value: DataItemCommitValue.value
        return self.committed_values[0].value

    def set_commit_value(self, value):
        # Value here is DataItemCommitValue type
        self.committed_values.appendleft(value)

    def get_temp_value(self):
        if not self.temp_value:
            raise RuntimeError(f"No present temp value for variable {self.name}")
        return self.temp_value.value


class SiteDataManager:
    '''
    Each site gets its own SiteDataManager.
    SDM stores:
    -the data of the site
    -the lock table for the site - each variable on the site has its own LockManager
    -status of the site
    '''

    def __init__(self, site_id: str):

        self.status = UP
        self.site_number = site_id
        self.data_dict = dict()
        self.lock_table = dict()
        # Tracking times the site failed and recovered -
        # In increasing order of time so latest failure at the end
        self.fail_timestamp_list = list()
        self.recover_timestamp_list = list()
        # Initialise site with DataItems
        self.initialise_site()

    def __repr__(self):
        return self.site_dump()

    def initialise_site(self):
        '''
        Every variable on site is stored in data_dict = {"x3": DataItem()}
        Every variable on site also has its own LockManager in lock_table = {"x3": LockManager()}
        '''

        for var in site_variables_init[self.site_number]:
            data_item_name = "x"+str(var)
            commit_val = DataItemCommitValue(str(var*10), 0)
            obj = DataItem(data_item_name, commit_val)
            lm = LockManager(data_item_name)
            # DataItem looks like--
            # self.name:"x3", self.committed_values: [DataItemCommitValue(value="30",commit_timestamp=0)]
            if var % 2 == 0:
                obj.replicated = True

            # "x3" : DataItem() object as above
            self.data_dict[data_item_name] = obj
            self.lock_table[data_item_name] = lm

    def check_membership(self, variable_name):
        '''
        Checks if a variable exists at this site.
        '''
        return True if variable_name in self.data_dict else False

    def site_status(self):
        return True if self.status == UP else False

    def read_snapshot(self, var, timestamp):
        '''
        * Read-Only transactions request a read-from-snapshot at the timestamp of when
        the R-O transaction started.
        * var : data item name - ex "x3"
        * timestamp : start timestamp of RO-transaction
        '''
        data_item: DataItem = self.data_dict[var]

        if data_item.readable():

            # Go over committed values and pick the one that is just before RO Transaction start
            # data_item.committed_values is a deque that stores latest commit value at index 0 -
            # and older commits to the right
            for cv in data_item.committed_values:

                # cv is DataItemCommitValue type
                if cv.commit_timestamp <= timestamp:

                    # process the first committed value with ts <= given ts

                    # If this variable is not replicated, success
                    if not data_item.is_replicated():
                        return Result(True, cv.value)

                    else:
                        # for replicated variables :
                        # If the site failed after the commit and before the transaction began, fail
                        # else success
                        for site_fail_time in self.fail_timestamp_list:
                            if cv.commit_timestamp < site_fail_time <= timestamp:
                                return Result(False, None)

                        # this site has not failed since commit and start of RO: success
                        return Result(True, cv.value)

        else:
            # If item isn't readable: fail
            return Result(False, None)

    def read(self, transaction_name, var):
        '''
           * Regular Read transaction.
           * Getting the Read lock + Reading both happens here.
           * var : data item name - ex "x3"
           * timestamp : start timestamp of RO-transaction
        '''

        data_item: DataItem = self.data_dict[var]
        lock_manager: LockManager = self.lock_table[var]

        # 1. Check if data item is readable
        if data_item.readable():

            present_lock = lock_manager.get_current_lock()
            # present_lock is either of ReadLock or WriteLock type

            # 2. Check if there's a lock on the item
            if present_lock:
                # There's a lock present on the variable.
                # Case 1: present lock is ReadLock
                if present_lock.lock == READ:

                    # Case 1.1 : this transaction is already in the transaction_set of ReadLock
                    if transaction_name in present_lock.transaction_set:
                        # Ok to read - this transaction already has read lock
                        return Result(True, data_item.get_committed_value())

                    # Case 1.2 : there are queued write locks already, and a read lock cannot skip over them
                    elif lock_manager.check_queued_write_locks(transaction_name):
                        # Add this read lock to the queue
                        lock_manager.add_to_lock_queue(QueueLock(transaction_name, var, READ))
                        return Result(False, None)

                    # Case 1.3 : This Read from transaction can use a shared read lock
                    else:
                        lock_manager.share_lock(transaction_name)
                        return Result(True, data_item.get_committed_value())

                # Case 2: There is a write lock on the variable.
                elif present_lock.lock == WRITE:

                    # Case 2.1 : The current write lock on the variable is held by the same
                    # transaction trying to read:
                    if transaction_name == present_lock.transaction_name:
                        # This basically means this transaction wrote to the variable, and now
                        # is reading what it wrote. We return the temp value and not the committed value.
                        return Result(True, data_item.get_temp_value())

                    # Case 2.2 : another transaction holds the write lock on the variable: so we wait
                    else:
                        lock_manager.add_to_lock_queue(QueueLock(transaction_name, var, READ))
                        return Result(False, None)

            else:
                # There is no lock currently on this variable - put a Read Lock on it
                lock_manager.set_lock(ReadLock(var, transaction_name))
                # Read
                return Result(True, data_item.get_committed_value())

        else:
            # Not readable - fail
            return Result(False, None)

    def fail(self, timestamp):
        pass

    def abort(self, transaction_name):
        pass

    def recover(self, timestamp):
        pass

    def commit(self, transaction_name, timestamp):
        pass

    def write_lock(self, transaction_name, data_item):
        return True

    def write(self, transaction_name, data_item, new_value):
        return

    def site_dump(self):
        output_string = "Site "
        output_string += self.site_number
        output_string += ": "+f"Status:[{'UP' if self.status else 'DOWN'}]"+" - "
        for data_item in self.data_dict.values():
            output_string += data_item.name+":"+data_item.get_committed_value()+", "

        return output_string[:-2]



