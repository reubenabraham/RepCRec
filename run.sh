rm LOG.txt
rm -rf tests/generatedOutput/
mkdir tests/generatedOutput/
for i in {1..32}
do
  printf "*******************************************************************************************************************\n"
  echo *****INPUT $i*****
  printf"\n\n"
  cat tests/testcases/test_$i.txt
  python3 main.py tests/testcases/test_$i.txt >> tests/generatedOutput/output_$i.txt
  printf "\n\n"
  echo ****OUTPUT $i****
  cat tests/generatedOutput/output_$i.txt
  printf "\n\n"
  diff tests/generatedOutput/output_$i.txt tests/expected_output/output_test_$i.txt >> LOG.txt
  # printf"\n\n"
  printf "*******************************************************************************************************************\n"
done

