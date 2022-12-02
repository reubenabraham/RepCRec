import pytest
import subprocess
import os
from tqdm import tqdm
import shutil

cwd = os.getcwd()
testcase_dir = cwd+"/tests/testcases/"
base_test_command = "python3 main.py "+testcase_dir
program_output_dir = cwd + "/tests/generated_output/"
expected_out_dir = cwd+"/tests/expected_output/"
testcases = sorted(os.listdir(testcase_dir))


def get_compare_list():
    expected_results = [expected_out_dir + f_name for f_name in sorted(os.listdir(expected_out_dir))]
    generated_results = [program_output_dir + f_name for f_name in sorted(os.listdir(program_output_dir))]
    res_list = []
    for i, j in zip(expected_results, generated_results):
        res_list.append((i, j))

    return res_list


COMPARE_LIST = get_compare_list()

# If you want to test two specific files, replace their names in file_list and replace
# COMPARE_LIST in the fixture with file_list
# file_list = [('/Users/reubenabraham/PycharmProjects/RepCRec/tests/expected_output/output_test_32.txt', '/Users/reubenabraham/PycharmProjects/RepCRec/tests/generated_output/output_test_32.txt')]


@pytest.mark.parametrize("expected,generated", COMPARE_LIST)
def test_outputs(expected, generated):
    exp = []
    gen = []
    print(f"Expected Output: ")
    for row in open(expected):
        print(row)
        exp.append(row)
    print("############### BREAK ###############")
    print(f"Generated Output: ")
    for row in open(generated):
        print(row)
        gen.append(row)
    assert exp == gen


def system_call(command: str):
    p = subprocess.Popen([command], stdout=subprocess.PIPE, shell=True)
    return p.stdout.read()


def create_program_output_dir(output_dir):
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)


def write_to_file(result, file_name):
    file = open(file_name, 'wb')
    file.write(result)
    file.close()


def remove_extra_files(expected_out, generated_out):
    for file in os.listdir(expected_out):
        if not file.startswith("output"):
            os.remove(expected_out+file)
    for file in os.listdir(generated_out):
        if not file.startswith("output"):
            os.remove(generated_out+file)


if __name__ == '__main__':

    # 1. Create new directory to put generated results
    create_program_output_dir(program_output_dir)

    # 2. Generate program output for all tests
    for test in tqdm(testcases):
        test_command = base_test_command+test
        result = system_call(test_command)
        write_to_file(result, program_output_dir+"output_"+test)

    # 3. Remove unwanted files:
    remove_extra_files(expected_out_dir, program_output_dir)

    # 4. Verify that both directories have files, then run pytest




