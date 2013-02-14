import os, sys, string, time
import subprocess
import re

from junitoutput import *
from ansi_color import ansiColor

def run(command) :
	print ansiColor.add_green_color(':: %s' % command)
	errorCode = os.system(command)
	if errorCode :
		print "\n\nThe following command failed:"
		print ansiColor.add_red_color(command)
		sys.exit()
	return not errorCode

def norun(command) :
	print ansiColor.add_red_color('XX %s' % command)

def phase(msg) :
    print ansiColor.add_brown_color("== %s" % msg)

def die(message, errorcode=-1) :
	print >> sys.stderr, message
	sys.exit(errorcode)

import diffaudio
import difftext
import diffbin
diff_for_type = {
	".wav" : diffaudio.differences,
	".txt" : difftext.differences,
	".clamnetwork" : difftext.differences,
	".xml" : difftext.differences,
	".ttl" : difftext.differences,
	".bin" : diffbin.differences,
}

def diff_files(expected, result, diffbase) :
	if not os.access(result, os.R_OK):
		print "Result file not found: ", result
		return ["Result was not generated: '%s'"%result]
	if not os.access(expected, os.R_OK):
		print "Expectation file not found for: ", result
		return ["No expectation for the output. First run? Check the results and accept them with the --accept option."]
	extension = os.path.splitext(result)[-1]

	diff = diff_for_type.get(extension, difftext.differences)
	return diff(expected, result, diffbase)


def archSuffix() :
	return string.strip(os.popen('uname -m').read())

def expectedArchName(base, extension='.wav') :
	suffix_arch = archSuffix()
	return base+'_expected_' + suffix_arch + extension

def expectedName(base, extension) :
	"""Returns the expected wav name.
	If an architecture specific output already exists, it will use it.
	"""
	expected = expectedArchName(base, extension)
	if os.access(expected,os.R_OK): return expected

	return base+'_expected'+extension

def badResultName(base, extension = '.wav') :
	return base+'_result'+extension

def diffBaseName(base) :
	return base+'_diff'

def prefix(datapath, case, output) :
	outputBasename = os.path.splitext(os.path.basename(output))[0]
	return os.path.join(datapath, case + '_' + outputBasename )

def accept(datapath, back2BackCases, archSpecific=False, cases=[]) :
	remainingCases = cases[:]
	for case, command, outputs in back2BackCases :
		if cases and case not in cases : continue
		if cases : remainingCases.remove(case)
		for output in outputs :

			extension = os.path.splitext(output)[-1]
			base = prefix(datapath, case, output)
			badResult = badResultName(base, extension)
			if not os.access(badResult, os.R_OK) : continue
			print "Accepting", badResult

			if archSpecific :
				os.rename(badResult, expectedArchName(base, extension))
			else :
				os.rename(badResult, expectedName(base, extension))
			try:
				os.remove(diffBaseName(base)+extension)
			except: 
				pass
	if remainingCases :
		print "Warning: No such test cases:", ", ".join("'%s'"%case for case in remainingCases)

def removeIfExists(filename) :
	try: os.remove(filename)
	except: pass

def passB2BTests(datapath, back2BackCases, testSuiteName, dry_run) :
	failedCases = []	
	
	testsuite = TestSuite(testSuiteName)
		

	if dry_run : 
		print "# DATAPATH=%s" % datapath
	for case, command, outputs in back2BackCases :
		if dry_run : 
			print "\n%s\n" % command
		else :
			testsuite.appendTestCase(passB2BTest(datapath, failedCases, case, command, outputs))

	
	junitDoc = JUnitDocument("AllTests")
	junitDoc.appendTestSuite(testsuite)

	junitFile = open(testSuiteName + "_test_detail.xml", "w")
	junitFile.write(junitDoc.toxml())
	junitFile.close()

	print "Summary:"
	print ansiColor.add_green_color('%i passed cases' % (len(back2BackCases)-len(failedCases)))

	if not failedCases : return True

	print ansiColor.add_red_color('%i failed cases!' % len(failedCases))
	for case, msgs in failedCases :
		print case, ":"
		for msg in msgs :
			print "\t%s"%msg
	return False


def passB2BTest(datapath, failedCases, case, command, outputs):
	testcase = TestCase(case)
	phase("Test: %s Command: '%s'"%(case,command))

	if isinstance(outputs, str) :
		outputs = [ outputs ]

	for output in outputs :
		removeIfExists(output)
	try :
		startTime = time.time()
		commandError = subprocess.call(command, shell=True)
		endTime = time.time()
		testcase.setTime(round(endTime-startTime, 2))
		if commandError :
			failedCases.append((case, ["Command failed with return code %i:\n'%s'"%(commandError,command)]))
			testcase.appendFailure("Command failed with return code %i:\n'%s'"%(commandError,command))
			return testcase
	except OSError, e :
		failedCases.append((case, ["Unable to run command: '%s'"%(command)]))
		testcase.appendFailure("Unable to run command: '%s'"%(command))
		return testcase
	failures = []
	for output in outputs :

		extension = os.path.splitext(output)[-1]
		base = prefix(datapath, case, output)
		expected = expectedName(base, extension)
		diffbase = diffBaseName(base)
		difference = diff_files(expected, output, diffbase)
		#diffbase = diffbase+'.wav'
		diffbase = diffbase + extension

		if not difference:
			print ansiColor.add_green_color(" Passed")
			removeIfExists(diffbase)
			removeIfExists(diffbase+'.png')
			removeIfExists(badResultName(base,extension))
		else:
			print ansiColor.add_red_color(" Failed")
			os.system('cp %s %s' % (output, badResultName(base,extension)) )
			failures.append("Output '%s':\n%s"%(base, '\n'.join(['\t- %s'%item for item in difference])))
			testcase.appendFailure("Output '%s':\n%s"%(base, '\n'.join(['\t- %s'%item for item in difference])))
		removeIfExists(output)
	if failures :
		failedCases.append((case, failures))

	return testcase

help ="""
To run the tests call this script without parameters.
	./back2back

To run just some cases you can use the "--filter substring" argument 
to run all tests cases which includes "substring" on its names, or "--filter_regex regex"
to run all tests cases which matches the regular expression "regex" on name:
	./back2back --filter dummy
(runs test cases called dummy_test case_dummy blahdummyblah etc..)
	./back2back --filter_regex ^dummy$
(runs only test case called "dummy")

To make a dry run to only print the commands use the argument --dry:
	./back2back --dry

Failed cases will generate *_result.wav and *_diff.wav
files for each missmatching output, containing the
obtained output and the difference with the expected one.

If some test fail but you want to accept the new results
just call:
	./back2back --accept case1 case2
where case1 and case2 are the cases to be accepted.

To know which are the available cases:
	./back2back --list

To accept any failing cases (USE IT WITH CARE) call:
	./back2back --acceptall

To accept some results but just for a given architecture,
due to floating point missmatches, use:
	./back2back --arch --accept case1 case2
"""

def _caseList(cases) :
	return "".join(["\t"+case+"\n" for case in cases])

def runBack2BackProgram_returnSuccess(datapath, argv, back2BackCases, testSuiteName="undefined", help=help, enable_colors=True) :

	"--help" not in sys.argv or die(help, 0)

	architectureSpecific = "--arch" in argv
	if architectureSpecific : argv.remove("--arch")
	ansiColor.USE_ANSI_COLORS = enable_colors

	os.access( datapath, os.X_OK ) or die(
		"Datapath at '%s' not available. "%datapath +
		"Check the back 2 back script on information on how to obtain it.")

	availableCases = [case for case, command, outputs in back2BackCases]

	if "--list" in argv :

		for case in availableCases :
			print case
		sys.exit()

	if "--accept" in argv :
		cases = argv[argv.index("--accept")+1:]
		cases or die("Option --accept needs a set of cases to accept.\nAvailable cases:\n"+"\n".join(["\t"+case for case, command, outputs in back2BackCases]))
		unsupportedCases = set(cases).difference(set(availableCases))
		if unsupportedCases:
			die("The following specified cases are not available:\n" + _caseList(unsupportedCases) + "Try with:\n" + _caseList(availableCases))
		accept(datapath, back2BackCases, architectureSpecific, cases)
		sys.exit()

	if "--acceptall" in argv :
		print "Warning: Accepting any faling case"
		accept(datapath, back2BackCases, architectureSpecific)
		sys.exit()

	if "--filter_regex" in argv :
		regex_pattern = argv[argv.index("--filter_regex")+1]
		allcases = list(back2BackCases)
		back2BackCases = [case for case in allcases if re.search(regex_pattern,case[0])]
		
	if "--filter" in argv :
		search_for = argv[argv.index("--filter")+1:]
		allcases = list(back2BackCases)
		back2BackCases = []
		for case in allcases:
			case_name = case[0]
			if any([ True for string in search_for if string in case_name ]) :
				back2BackCases.append(case)
	if "--negative_filter" in argv :
		search_for = argv[argv.index("--filter")+1:]
		allcases = list(back2BackCases)
		back2BackCases = []
		for case in allcases:
			case_name = case[0]
			if not any([ True for string in search_for if string in case_name ]) :
				back2BackCases.append(case)
	dry_run = False
	if "--dry" in argv : 
		dry_run = True

	return passB2BTests(datapath, back2BackCases, testSuiteName, dry_run)

def runBack2BackProgram(datapath, argv, back2BackCases, testSuiteName="undefined", help=help, enable_colors=True) :
	runBack2BackProgram_returnSuccess(datapath, argv, back2BackCases, testSuiteName, help, enable_colors) or die("Tests not passed") 

### End of generic stuff
