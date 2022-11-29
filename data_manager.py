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
    def __init__(self, name: str, value):
        self.name = name
        # Need to store all committed values because for RO transactions, we have to pick up commited
        # value at a certain time. Latest committed value at the left, and older ones after
        # the value variable is of DataItemCommitValue type
        self.committed_values = deque()
        self.committed_values.appendleft(value)
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
        # Gets presently committed value
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
        self.initialise_site()

    def __repr__(self):
        return self.site_dump()

    def initialise_site(self):
        '''
        Set initial variable values for this site
        '''

        for var in site_variables_init[self.site_number]:
            data_item_name = "x"+str(var)
            commit_val = DataItemCommitValue(str(var*10), 0)
            obj = DataItem(data_item_name, commit_val)
            # DataItem looks like--
            # self.name:"x3", self.committed_values: [DataItemCommitValue(value="30",commit_timestamp=0)]
            if var % 2 == 0:
                obj.replicated = True

            # "x3" : DataItem() object as above
            self.data_dict[data_item_name] = obj

    def check_membership(self, variable_name):
        '''
        Checks if a variable exists at this site.
        '''
        return True if variable_name in self.data_dict else False

    def site_status(self):
        return True if self.status == UP else False

    def fail(self, timestamp):
        pass

    def abort(self, transaction_name):
        pass

    def recover(self, timestamp):
        pass

    def commit(self, transaction_name, timestamp):
        pass

    def read(self, transaction_name, data_item):
        return Result(True, "10")

    def read_snapshot(self, data_item, timestamp):
        return Result(True, "20")

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



