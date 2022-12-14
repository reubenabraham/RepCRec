from collections import namedtuple

READ = "R"
WRITE = "W"
BEGIN = "begin"
BEGIN_RO = "beginRO"
END = "end"
FAIL = "fail"
RECOVER = "recover"
DUMP = "dump"
UP = 1
DOWN = 0

site_variables_init = {
    "1": [2, 4, 6, 8, 10, 12, 14, 16, 18, 20],
    "2": [1, 2, 4, 6, 8, 10, 11, 12, 14, 16, 18, 20],
    "3": [2, 4, 6, 8, 10, 12, 14, 16, 18, 20],
    "4": [2, 3, 4, 6, 8, 10, 12, 13, 14, 16, 18, 20],
    "5": [2, 4, 6, 8, 10, 12, 14, 16, 18, 20],
    "6": [2, 4, 5, 6, 8, 10, 12, 14, 15, 16, 18, 20],
    "7": [2, 4, 6, 8, 10, 12, 14, 16, 18, 20],
    "8": [2, 4, 6, 7, 8, 10, 12, 14, 16, 17, 18, 20],
    "9": [2, 4, 6, 8, 10, 12, 14, 16, 18, 20],
    "10": [2, 4, 6, 8, 9, 10, 12, 14, 16, 18, 19, 20],
}

# Namedtuples :
DeadlockResult = namedtuple('DeadlockResult', 'is_deadlock transaction_name')
Result = namedtuple('Result', 'success value')
DataItemCommitValue = namedtuple('DataItemCommitValue', 'value commit_timestamp')
DataItemTempValue = namedtuple('DataItemTempValue', 'value transaction_name')
OperationResult = namedtuple('OperationResult', 'success value')
