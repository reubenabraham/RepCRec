Steps To Reprounzip the .rpz file

1. Download the reprofiles folder if you haven't already
   The link is available here 
   http://cs.nyu.edu/courses/fall21/CSCI-GA.2434-001/reprofiles.zip

2. Upload this folder to the CIMS server

3. On CIMS, cd reprofiles

4. Run chmod +x reprounzip

5. Assuming the .rpz file is in the same directory, run
   ./reprounzip directory setup ADB_Project.rpz ~/adb_unreprofiles
   
   If you encounter an error here, run the following command
   export LC_ALL=C

6. Run ./reprounzip directory run ~/adb_unreprofiles/

You should see the output of the program now. 
The program runs 32 tests cases and shows the input and output for every test case.


Steps to Run the shell script

We provide a run.sh script to execute 32 test cases. 
After you reprounzip the file on CIMS using the above steps, 
you can find the shell script in the following directory
~/adb_unreprofiles/root/home/<net-id>/ADB/Project/
(The net-id used above is sd4495)

1. ./run.sh

The executable should be available. If not, run chmod +x run.sh and then try step 1.


Steps to Run Python program

1. cd into ADB/Project/

2. Run python3 main.py <input.txt>