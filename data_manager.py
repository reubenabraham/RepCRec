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
        return self.name+f"= {self.get_committed_value()}"

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
                    elif lock_manager.check_any_queued_write_locks():
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

    def test_write_lock(self, transaction_name, var):
        '''
        This function attempts to acquire a write-lock on the data-item on
        this site, for this transaction.
        Return: True if it can write lock, False if it can not
        transaction_name: "T1"
        var: "x3"
        '''

        lock_manager: LockManager = self.lock_table[var]
        present_lock = lock_manager.get_current_lock()
        if present_lock:
            # There's a lock present on this data-item
            # Case 1: Present lock is Read Lock

            if present_lock.lock == READ:
                # Case 1.1 there are multiple transactions holding this read lock: must wait: fail
                if len(present_lock.transaction_set) != 1:
                    lock_manager.add_to_lock_queue(QueueLock(transaction_name, var, WRITE))
                    return False

                # Case 1.2: a single transaction holds the R lock and is same as the requesting transaction
                elif transaction_name in present_lock.transaction_set:

                    # If there are no other queued write lock requests from other transactions,
                    # then promote to write lock
                    if not lock_manager.check_queued_write_locks(transaction_name):
                        return True
                    else:
                        # Cannot skip ahead of the other write lock reqs- wait- fail
                        lock_manager.add_to_lock_queue(QueueLock(transaction_name, var, WRITE))
                        return False

                # Case 1.3 - another transaction holds the read lock - wait- fail
                else:
                    lock_manager.add_to_lock_queue(QueueLock(transaction_name, var, WRITE))
                    return False

            # Case 2: Present lock is a Write Lock
            elif present_lock.lock == WRITE:
                # Case 2.1  Write lock is already held by the requesting transaction: success
                if present_lock.transaction_name == transaction_name:
                    return True
                # Case 2.2 Write lock is held by another transaction: must wait: fail
                else:
                    lock_manager.add_to_lock_queue(QueueLock(transaction_name, var, WRITE))
                    return False

        else:
            # No lock on this variable- we can lock ourselves
            return True

    def write(self, transaction_name, var, new_value):
        '''
        This function checks if locks can be acquired by calling test_write_locks()
        and executes the Write.
        test_write_locks has already done the validations and queued WLs, so we raise errors on
        any path that doesn't give us WLs
        transaction_name : "T1"
        data_item: "x3"
        new_value: "45"
        None return
        '''

        data_item: DataItem = self.data_dict[var]
        lock_manager: LockManager = self.lock_table[var]
        present_lock = lock_manager.get_current_lock()

        if present_lock:
            # There's currently a lock on var- check what type
            # Case 1: Read Lock
            if present_lock.lock == READ:
                # Case 1.1 - multiple transactions have read locks on the variable - fail
                if len(present_lock.transaction_set) != 1:
                    raise RuntimeError(
                        f"Multiple transactions hold RL on {present_lock.data_item}.{self.site_number}- cant WL")

                # Case 1.2: same transaction holds RL
                elif transaction_name in present_lock.transaction_set:
                    # Same transaction holds the RL- see if we can promote
                    if lock_manager.check_queued_write_locks(transaction_name):
                        raise RuntimeError(f"Other transaction WL in queue- cant promote: site:{self.site_number}")
                    else:
                        # promote RL -> WL
                        lock_manager.promote_lock(WriteLock(var, transaction_name))

                # Case 1.3- another transaction holds RL
                else:
                    # Another transaction holds the RL -
                    raise RuntimeError(f"Another transaction holds RL- cant promote to WL: site:{self.site_number}")

            # Case 2: Write Lock
            elif present_lock.lock == WRITE:

                # Case 2.1 this transaction already holds the write lock - write
                if transaction_name == present_lock.transaction_name:
                    data_item.temp_value = DataItemTempValue(new_value, transaction_name)
                    return
                else:
                    # Another transaction holds write lock- we should not hit this code path
                    # if test_write_lock returned True - meaning it was able to validate it can lock all items
                    raise RuntimeError(
                        f"Another transaction {present_lock.transaction_name} holds the WL to {present_lock.data_item}.{self.site_number}")

        else:
            # No present locks on var- set lock & set temp value for var
            lock_manager.set_lock(WriteLock(var, transaction_name))
            data_item.temp_value = DataItemTempValue(new_value, transaction_name)
            return

    def abort(self, transaction_name):
        '''
        * Transaction has to abort- site went down after transaction touched it
        * Release all locks held by transaction
        * transaction_name = "T1"
        * return None
        '''

        for lock_manager in self.lock_table.values():

            lock_manager.release_current_lock(transaction_name)
            # Check for and remove any queued locks for this transaction
            for queued_lock in list(lock_manager.lock_queue):
                if queued_lock.transaction_name == transaction_name:
                    lock_manager.lock_queue.remove(queued_lock)

        self.process_lock_queues()

    def process_lock_queues(self):
        '''
        * Goes over the lock_queues for all the lock table members
        and gives the lock to the member next in line.
        * This is necessary because transactions either commit or abort
        and when locks are freed up, they're given to next in the queue.
        * Also, in the new lock is a READ, makes sure all the other reads in queue are shared
        * And for the first write in queue and its the same transaction, will promote the current READ -> WL
        '''

        for data_item_name, lock_manager in self.lock_table.items():

            # Only required if there are QueuedLocks in queue
            if len(lock_manager.lock_queue) == 0:
                continue
            else:
                present_lock = lock_manager.get_current_lock()
                # Case 1: If there are no present locks, give it to next in queue
                if not present_lock:
                    next_queued_lock = lock_manager.lock_queue.pop(0)
                    if next_queued_lock.lock == WRITE:
                        lock_manager.set_lock(WriteLock(next_queued_lock.data_item, next_queued_lock.transaction_name))
                    elif next_queued_lock.lock == READ:
                        lock_manager.set_lock(ReadLock(next_queued_lock.data_item, next_queued_lock.transaction_name))

                # A new present lock might have been set from the above statements
                present_lock = lock_manager.get_current_lock()
                # Share all other read locks in queue with this read lock until we see a WL
                if present_lock.lock == READ:

                    for queued_lock in list(lock_manager.lock_queue):

                        if queued_lock.lock == READ:
                            # All read locks can be shared with read lock currently on data item
                            lock_manager.share_lock(queued_lock.transaction_name)
                            lock_manager.lock_queue.remove(queued_lock)

                        elif queued_lock.lock == WRITE:
                            # See if we promote current read lock to write lock
                            # If the transaction of the currently held lock == the queued write lock
                            if len(lock_manager.current_lock.transaction_set) == 1 and queued_lock.transaction_name in lock_manager.current_lock.transaction_set:
                                # Promote the current Read lock to a Write lock.
                                lock_manager.promote_lock(WriteLock(queued_lock.data_item, queued_lock.transaction_name))
                                lock_manager.lock_queue.remove(queued_lock)

                            # Since no more read locks can skip over this write in queue
                            # break the loop
                            break

        return

    def commit(self, transaction_name, timestamp):
        '''
        * When a transaction commits, we release all its locks and
        commit the DataItemTempValue -> DataItemCommitValue
        * transaction_name: "T1"
        * timestamp:int = 3
        * returns None
        '''

        # Step 1: release held locks
        for lock_manager in self.lock_table.values():
            lock_manager.release_current_lock(transaction_name)
            for queued_lock in list(lock_manager.lock_queue):
                if queued_lock.transaction_name == transaction_name:
                    raise RuntimeError(f"{transaction_name} cannot commit with pending lock requests")

        # Step 2: commit values
        for data_item in self.data_dict.values():
            if data_item.temp_value and transaction_name == data_item.temp_value.transaction_name:
                data_item.set_commit_value(DataItemCommitValue(data_item.temp_value.value, timestamp))
                data_item.can_read = True

        # For any released locks, move other locks ahead
        self.process_lock_queues()

    def fail(self, timestamp):
        '''
        * Clear the lock table
        * Set site to DOWN
        * Track the time the site failed
        '''

        for lock_manager in self.lock_table.values():
            lock_manager.clear_locks()

        self.status = DOWN
        self.fail_timestamp_list.append(timestamp)
        return

    def recover(self, timestamp):
        '''
        * Site recovers at time = timestamp
        * Set site status back UP
        * Make sure replicated variables no longer respond to any writes.
        * Track timestamp when the site came back up.
        '''
        self.recover_timestamp_list.append(timestamp)
        self.status = UP
        for data_item in self.data_dict.values():
            if data_item.is_replicated():
                data_item.can_read = False
        return

    def site_dump(self):
        output_string = f"Status:{'UP' if self.status else 'DOWN'}: "
        output_string += "site "
        output_string += self.site_number
        output_string += "- "
        for data_item in self.data_dict.values():
            output_string += data_item.name+":"+data_item.get_committed_value()+", "

        return output_string[:-2]

    @staticmethod
    def current_lock_blocks(current_lock, queued_lock):
        '''
        Returns True if the current lock is blocking a queued lock
        '''
        if current_lock.lock == WRITE:
            if current_lock.transaction_name == queued_lock.transaction_name:
                return False
            else:
                return True
        elif current_lock.lock == READ:
            if len(current_lock.transaction_set) == 1 and queued_lock.transaction_name in current_lock.transaction_set:
                return False
            elif queued_lock.lock == READ:
                return False
            else:
                return True

    @staticmethod
    def queued_lock_blocks(left_queued_lock, right_queued_lock):
        '''
        * Returns True if a queued lock 1, ahead of queued lock 2, blocks queued lock 2
        * Note that left_queued_lock is ahead of right_queued_lock
        '''
        if left_queued_lock.lock == WRITE or right_queued_lock.lock == WRITE:
            if left_queued_lock.transaction_name == right_queued_lock.transaction_name:
                return False
            else:
                return True
        elif left_queued_lock.lock == READ and right_queued_lock.lock == READ:
            return False

    def return_waits_for_graph(self):
        '''
        * Returns the blocking graph for this site.
        * There is a (possible) current_lock, and (possible) queued locks [a,b,c,d]
        * cur_lock : [a,b,c,d]
        * first find possible edges from a->cur_lock, b->cur_lock ...
        * then find edges from b->a, c->a, c->b (older to newer queued lock)
        * add both to blocking graph
        '''

        waits_graph = defaultdict(set)

        for data_item, lock_manager in self.lock_table.items():

            # If there are no locks in queue, check next data_item
            if (not lock_manager.current_lock) or len(lock_manager.lock_queue) == 0:
                continue

            else:
                # There is a lock queue for this data_item: each item in the queue is QueueLock class type
                # Case 1: Add edges from queued locks -> current lock
                for queued_lock in lock_manager.lock_queue:

                    if self.current_lock_blocks(lock_manager.current_lock, queued_lock):

                        # Case 1.1: current lock is a write lock.
                        if lock_manager.current_lock.lock == WRITE:
                            # Any transaction thats not the current transaction should be blocking.
                            if lock_manager.current_lock.transaction_name != queued_lock.transaction_name:
                                # Add edge in graph. queued lock transaction -> current lock transaction.
                                waits_graph[queued_lock.transaction_name].add(lock_manager.current_lock.transaction_name)

                        # Case 1.2: current lock is a read lock
                        elif lock_manager.current_lock.lock == READ:
                            # the queued lock is blocked by :
                            # any transaction in the current_lock.transaction_set thats not itself. - since
                            # multiple transactions can hold read lock.
                            for cur_lock_ts in lock_manager.current_lock.transaction_set:
                                if queued_lock.transaction_name != cur_lock_ts:
                                    waits_graph[queued_lock.transaction_name].add(cur_lock_ts)

                # Case 2: Add edges from queued locks to queued locks.
                # For example- lock_queue = [a,b,c,d] - there could be an edge from d -> b
                for right_ind in range(len(lock_manager.lock_queue)):
                    for left_ind in range(right_ind):
                        if self.queued_lock_blocks(lock_manager.lock_queue[left_ind], lock_manager.lock_queue[right_ind]):
                            # edge from right_index_ql -> left_index_ql
                            waits_graph[lock_manager.lock_queue[right_ind].transaction_name].add(lock_manager.lock_queue[left_ind].transaction_name)

        return waits_graph




