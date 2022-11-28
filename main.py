import sys
from input_processing import InputProcessor

from transaction_manager import Transaction
from data_manager import SiteDataManager
from transaction_manager import TransactionManager

if __name__ == "__main__":

    input_processor = InputProcessor(len(sys.argv), sys.argv)
    instruction_queue = input_processor.create_instruction_queue()
    print(instruction_queue)

    tm = TransactionManager()

    tm.simulation(instruction_queue)
    tm.print_transaction_db()
    tm.print_event_queue()

