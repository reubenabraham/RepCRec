from typing import List
import os.path
import errno
from parser.InputClasses import Read_IO, Write_IO, Begin_IO, BeginRO_IO, End_IO, Recover_IO, Fail_IO, Dump_IO
from constants import READ, RECOVER, BEGIN, BEGIN_RO, FAIL, DUMP, END, WRITE
from collections import deque


class InputProcessor:

    def __init__(self, number_of_params: int, params_list: List):
        self.number_of_params = number_of_params
        self.params_list = params_list
        self.file_path = self.read_cmd_params()

    def read_cmd_params(self) -> str:
        '''
        Reads and returns file_path passed as a cmd line arg when invoking main()
        '''
        if self.number_of_params <= 1:
            raise Exception("Please provide a test file.")
        if self.number_of_params > 2:
            raise Exception("Too many invocation parameters")

        file_path = self.params_list[1]

        if not os.path.exists(file_path):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), file_path)

        return file_path

    @staticmethod
    def unpack_tuple_str(s: str):
        '''
        Converts '(a,b,c)' -> tuple(a,b,c)
        '''
        # Remove all spaces in the tuple string
        st = s[1:-1].replace(" ", "")
        return tuple(x for x in st.split(','))

    @staticmethod
    def validate_tuple_length(tup, expected_size, line_count, line):
        '''
        Raises an exception if it unpacks more/less than expected.
        '''
        if len(tup) != expected_size:
            raise Exception(f"Invalid input at line {line_count}: {line}")

    def create_instruction_queue(self):

        instruction_queue = deque()

        with open(self.file_path) as fp:
            lines = fp.readlines()
            line_count = 0
            for line in lines:
                line_count += 1
                line = line.strip()
                if not line or line.startswith('/'):
                    continue

                # Removes comments at end of the line
                line = line.split(')')[0] + ')'

                if line.startswith('R(') and line.endswith(')'):
                    r = self.unpack_tuple_str(line[1:])
                    self.validate_tuple_length(r, 2, line_count, line)
                    transaction, variable = r
                    read_obj = Read_IO(transaction, variable)
                    instruction_queue.append((READ, read_obj))

                elif line.startswith('W(') and line.endswith(')'):
                    w = self.unpack_tuple_str(line[1:])
                    self.validate_tuple_length(w, 3, line_count, line)
                    transaction, variable, new_variable_value = w
                    write_obj = Write_IO(transaction, variable, new_variable_value)
                    instruction_queue.append((WRITE, write_obj))

                elif line.startswith('fail(') and line.endswith(')'):
                    f = self.unpack_tuple_str(line.lstrip('fail'))
                    self.validate_tuple_length(f, 1, line_count, line)
                    fail_site = f[0]
                    fail_obj = Fail_IO(fail_site)
                    instruction_queue.append((FAIL, fail_obj))

                elif line.startswith('recover(') and line.endswith(')'):
                    re = self.unpack_tuple_str(line.lstrip('recover'))
                    self.validate_tuple_length(re, 1, line_count, line)
                    recover_site = re[0]
                    recover_obj = Recover_IO(recover_site)
                    instruction_queue.append((RECOVER, recover_obj))

                elif line.startswith('begin(') and line.endswith(')'):
                    b = self.unpack_tuple_str(line.lstrip('begin'))
                    self.validate_tuple_length(b, 1, line_count, line)
                    transaction = b[0]
                    begin_obj = Begin_IO(transaction)
                    instruction_queue.append((BEGIN, begin_obj))

                elif line.startswith('beginRO(') and line.endswith(')'):
                    bro = self.unpack_tuple_str(line.lstrip('beginRO'))
                    self.validate_tuple_length(bro, 1, line_count, line)
                    transaction = bro[0]
                    begin_ro_obj = BeginRO_IO(transaction)
                    instruction_queue.append((BEGIN_RO, begin_ro_obj))

                elif line.startswith('end(') and line.endswith(')'):
                    e = self.unpack_tuple_str(line.lstrip('end'))
                    self.validate_tuple_length(e, 1, line_count, line)
                    transaction = e[0]
                    end_obj = End_IO(transaction)
                    instruction_queue.append((END, end_obj))

                elif line == "dump()":
                    dump_obj = Dump_IO()
                    instruction_queue.append((DUMP, dump_obj))

                else:
                    raise Exception(f"Invalid input at line {line_count}: {line}")

        return instruction_queue
