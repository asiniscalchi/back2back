back2back - Light framework to setup back-to-back test scripts
==============================================================

This software is helpfull to prepare and managing a set 
of back2back test scripts over any piece of software 
that can be called and controlled by command line and
produces output files that can be compared against
some other reference files.

They were initially developed to do b2b tests on audio
processing algorithms by comparing audio files but now 
it is extended to many other kind of files, like plain
text and xml. Other formats can be added by extensions.

Why back-to-back testing
------------------------

A Back-to-back tests is a black box tests that just compares
that, given an input, you have the same output all the time.
Unit testing and Test Driven Development are a quite more
preferable strategy to test a piece of software.
But often we need to change a piece of software which has
been developed without proper testing.
A quick way to get control over it is setting up a set of
back-to-back tests and then proceeding with the
refactoring with a larger level of confidence than having
no test at all.

**Note of warning:**
Don't feel too confident by being backed by back2back tests.
It is black-box testing, so it is hard to ensure full coverage.
You may be changing a behaviour which is not exercised
by the b2b test, and not noticing.


How this tool helps
-------------------

If b2b tests are hard to run and maintain,
they will get old and useless.
This script automates most tedious back2back
related task such as setting up, verifying results,
accepting changes, clearing data...

Features:
* It is auto-checked, like most Xunit frameworks
* It automagically manages the expectation data
* On failure, it generates handy data to evaluate
	the changes by providing diffs and keeping
	failed and expected data for reference.
* Provides a handy command line to accept failed 
  results as proper ones.
* When the test turns green or it is accepted all 
  failure related data gets cleared.
* The SUT can be any shell command line (with pipes, sequences...)
* Comparators and diff generators can be added for your own file type.
* Allows to specify architecture dependant outputs for the same test.

Install
-------
On ubuntu 12.04 machine you will need to install the following packages:

	$ sudo apt-get install python-setuptools
	$ sudo easy_install scikits.audiolab
	
Then get the back2back framework and within the back2back directory:

	$ setup.py install --user

How does it works
-----------------

A b2b test is a python script which defines a set of tests.
For each test you want to run, you need to define:
* A name
* A command line
* A set of output files to check

Just like in this b2b script:

	#!/usr/bin/python
	import sys
	from b2btest import runBack2BackProgram

	data_path="path/to/b2bdata"
	back2BackTests = [
		("myprogram_with_option",
				"./myprogram --option input1.wav input2.wav output.wav otheroutput.wav",
				["output.wav",	"otheroutput.wav"]),
				
		("myprogram_with_other_option",	"./myprogram --other-option input.wav output.wav", "output.wav"),
		]
	runBack2BackProgram(data_path, sys.argv, back2BackTests, "test_suite_name")

Save this file as `back2back`, for example, and make it executable.

To run the tests call this script without parameters.

	./back2back

If you want to run just some specific cases you can use the following command line arguments:

"--filter substring" : runs all tests cases which includes "substring" on its names

	./back2back --filter dummy # (runs test cases called dummy_test case_dummy blahdummyblah etc..)
	
"--filter_regex regex" : runs all tests cases which matches the regular expression "regex" on name

	./back2back --filter_regex ^dummy$ # (runs only test case called "dummy")

Failed cases will generate `*_result.wav` and `*_diff.wav`
files for each mismatching output, containing the
obtained output and the difference with the expected one.

If some test fail but you want to accept the new results
just call:

	./back2back --accept case1 case2

where `case1` and `case2` are the cases to be accepted.

To know which are the available cases:

	./back2back --list

To accept any failing cases (USE IT WITH CARE) call:

	./back2back --acceptall

To accept some results but just for a given architecture,
due to floating point mismatches, use:

	./back2back --arch --accept case1 case2



JUnit Output
------------
At every execution the back2back framework will create an test_suite_name_test_detail.xml file in in JUnit format


