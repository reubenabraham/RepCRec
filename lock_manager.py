from constants import READ, WRITE


class ReadLock:
    def __init__(self, data_item: str, transaction_name: str):
        self.data_item = data_item
        # Multiple transactions can share a read-lock
        self.transaction_set = {transaction_name}
        self.lock = READ

    def __repr__(self):
        return f"[Read lock on {self.data_item}, Shared by : {self.transaction_set}]"


class WriteLock:

    def __init__(self, data_item: str, transaction_name: str):
        self.data_item = data_item
        # Only a single transaction can hold a write lock on a data_item
        self.transaction_name = transaction_name
        self.lock = WRITE

    def __repr__(self):
        return f"[Write Lock on {self.data_item}, held by {self.transaction_name}]"


class QueueLock:

    def __init__(self, transaction_name: str, data_item: str, lock_type):
        self.transaction_name = transaction_name
        self.data_item = data_item
        self.lock = lock_type

    def __repr__(self):
        return f"[{self.transaction_name} with {self.lock} lock on {self.data_item} in queue]"


class LockManager:
    '''
    Each variable has a lock manager to manage locks on it.
    '''
    def __init__(self, variable: str):
        self.data_item = variable
        self.current_lock = None
        self.lock_queue = list()

    def set_lock(self, lock):
        # lock here is either ReadLock or WriteLock
        self.current_lock = lock

    def share_lock(self, transaction_name):
        # Only read-locks can be shared by transactions
        if self.current_lock.lock == READ:
            self.current_lock.transaction_set.add(transaction_name)

        else:
            raise RuntimeError("# Cant share write locks #")

    def get_current_lock_type(self):
        if not self.current_lock:
            raise RuntimeError(f"No lock currently on {self.data_item}")
        else:
            return self.current_lock.lock

    def clear_locks(self):
        # Clear all locks
        self.current_lock = None
        self.lock_queue = list()

    def add_to_lock_queue(self, additional_lock):
        # additional_lock is of type QueueLock
        # queued_lock is of type QueueLock

        for queued_lock in self.lock_queue:
            if (queued_lock.transaction_name == additional_lock.transaction_name) and ((queued_lock.lock == additional_lock.lock) or (additional_lock.lock == READ)):
                # If the additional lock's transaction already has a lock in queue that the same type or
                # the additional locks lock type = READ. Because then since the first condition satisfied,
                # and the second one did not- this means the transaction already has a write lock in queue
                # and all write locks have READ authority. Do nothing for this case.
                return

        # if flow reaches here, lock needs to be added:
        self.lock_queue.append(additional_lock)

    def promote_lock(self, new_lock):
        # Promoting a read -> write lock
        # new_lock is of WriteLock type

        # Validate if it is possible to do this.
        # 1. Make sure there's a lock to begin with
        if not self.current_lock:
            raise RuntimeError(f"No locks currently on {self.data_item}.")

        # 2. Make sure current lock is a READ
        if not self.current_lock.lock == READ:
            raise RuntimeError("Current lock needs to be READ lock to be promoted.")

        # 3. If other transactions have shared read locks on the data item, cannot promote.
        if len(self.current_lock.transaction_set) != 1:
            raise RuntimeError("Cannot promote when lock is shared by other transactions.")

        # 4. Make sure the transaction of new_lock already holds a read lock on the data_item
        if new_lock.transaction_name not in self.current_lock.transaction_set:
            raise RuntimeError(f"Cannot promote because {new_lock.transaction_name} does not hold a read lock on {self.current_lock.data_item}")

        # All checks done, promote lock -
        self.set_lock(new_lock)

    def check_queued_write_locks(self, transaction_name):
        # Go over queued locks to see if there are any other write locks
        # That are NOT from transaction_name
        for queued_lock in self.lock_queue:
            if queued_lock.lock == WRITE and queued_lock.transaction_name != transaction_name:
                return True

        return False

    def release_current_lock(self, transaction_name):
        # Releases the current lock held by transaction_name.
        # Since multiple read locks can be held on a variable at the same time,
        # We specify which transaction's locks to release.
        if self.current_lock:
            if self.current_lock.lock == WRITE:
                # There can only be one transaction with it
                if self.current_lock.transaction_name == transaction_name:
                    self.current_lock = None

            elif self.current_lock.lock == READ:
                # Read locks can be shared.
                if transaction_name in self.current_lock.transaction_set:
                    self.current_lock.transaction_set.remove(transaction_name)
                    if len(self.current_lock.transaction_set) == 0:
                        self.current_lock = None
