import sys
from input_processing import InputProcessor
from constants import READ, RECOVER, WRITE, FAIL, BEGIN, BEGIN_RO, DUMP, END
from transaction_manager import Transaction
from data_manager import SiteDataManager
from transaction_manager import TransactionManager

if __name__ == "__main__":

    input_processor = InputProcessor(len(sys.argv), sys.argv)
    event_queue = input_processor.create_event_queue()
    EVENT_TIME = 0

    '''
    * The main simulation happens here. The event queue has events ordered as per the input file.
    * No look-ahead happens in the event_queue- events are processed as they come.
    '''

    '''
    while event_queue:
        operation, obj = event_queue.popleft()

        if operation == BEGIN or operation == BEGIN_RO:
            obj = Transaction(obj.transaction, EVENT_TIME)
            if operation == BEGIN_RO:
                obj.set_read_only()

            print(obj)

        EVENT_TIME += 1

    '''

    tm = TransactionManager()
    print(tm.SDMs["1"])
