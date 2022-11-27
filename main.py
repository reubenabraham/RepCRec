import sys
from input_processing import InputProcessor

if __name__ == "__main__":

    input_processor = InputProcessor(len(sys.argv), sys.argv)
    event_queue = input_processor.create_event_queue()
    while event_queue:
        operation, obj = event_queue.popleft()
        print(operation, obj)

