rm LOG.txt
rm -rf tests/generated_output_shell_script/
mkdir tests/generated_output_shell_script/
for i in {1..32}
do
  printf "*******************************************************************************************************************\n"
  echo *****INPUT $i*****
  printf"\n\n"
  cat tests/testcases/test_$i.txt
  python3 main.py tests/testcases/test_$i.txt >> tests/generated_output_shell_script/output_$i.txt
  printf "\n\n"
  echo ****OUTPUT $i****
  cat tests/generated_output_shell_script/output_$i.txt
  printf "\n\n"
  diff tests/generated_output_shell_script/output_$i.txt tests/expected_output/output_test_$i.txt >> diff_log.txt
  printf "*******************************************************************************************************************\n"
done

