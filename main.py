import sys
from parser.input_processing import InputProcessor
from managers.transaction_manager import TransactionManager

if __name__ == "__main__":

    input_processor = InputProcessor(len(sys.argv), sys.argv)
    instruction_queue = input_processor.create_instruction_queue()
    print("Instruction Queue: ")
    print(instruction_queue)
    print("\nExecution:")

    tm = TransactionManager()
    tm.simulation(instruction_queue)

