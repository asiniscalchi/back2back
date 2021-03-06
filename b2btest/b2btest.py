import os, sys, string, time
import subprocess
import re

from junitoutput import *
from ansi_color import ansiColor
from shutil import copyfile
import platform


def getDataPathFromEnvironmentVarOrFile (dataPathEnvVar, dataPathDefFile, suiteSubDir ) :
	"""
	Get the data path, parsing the file dataPathDefFile and the environment variable dataPathEnvVar. The last overrides the first.
	"""
	try:
		baseDataPath = os.environ[dataPathEnvVar].strip()
		if not baseDataPath : raise(KeyError)
		dataPath = os.path.join(baseDataPath, suiteSubDir)
	except KeyError:
		try:
			baseDataPath = open(dataPathDefFile,"r").read().strip()
			dataPath = os.path.join(baseDataPath, suiteSubDir)
		except: 
			print "(EE) Please set the environment variable %s" % dataPathEnvVar
			return None
			sys.exit(1)
		print "%s environment variable not set. Using \"%s\" from %s" % (dataPathEnvVar, baseDataPath, dataPathDefFile)
	else:
		print "Using environment variable %s = \"%s\"" % (dataPathEnvVar, baseDataPath)

	if not os.path.isdir(dataPath) :
		print("(EE) %s is not a directory" % dataPath)
		return None

	return dataPath

def splitCmdLineArguments(args) : 
	"""
	Separate command line arguments: all the arguments before an optional "--" would be applied to the test commands, while the arguments after that would be applied to the b2b inftastructure
	"""
	separatorIdx = args.index("--") if "--" in args else len(args)
	b2bArgs = args[:separatorIdx]
	cmdArgs = [] if separatorIdx == len(args) else args[separatorIdx+1:]
	return { "cmdArgs" : cmdArgs, "b2bArgs" : b2bArgs } 

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
import diffColumnsWithDelta
diff_class_for_type = {
	".wav" : diffaudio.DiffAudio,
	".audio" : diffaudio.DiffAudio,
	".clamnetwork" : difftext.DiffText,
	".xml" : difftext.DiffText,
	".ttl" : difftext.DiffText,
	".bin" : diffbin.DiffBin,
	".txt" : diffColumnsWithDelta.DiffColumnsWithDelta,
	".metadata" : diffColumnsWithDelta.DiffColumnsWithDelta,
}

def diff_files(expected, result, diffbase, extra_args_for_diff) :
	if not os.access(result, os.R_OK):
		print "Result file not found: ", result
		return ["Result was not generated: '%s'"%result]
	if not os.access(expected, os.R_OK):
		print "Expectation file not found for: ", result
		return ["No expectation for the output. First run? Check the results and accept them with the --accept option."]
	extension = os.path.splitext(result)[-1]

	diffClass = diff_class_for_type.get(extension, difftext.DiffText)
	return diffClass().differences(expected, result, diffbase, extra_args_for_diff)


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
def listFailedCases(datapath, back2BackCases) :
	failedCases = []
	for test in back2BackCases :
		case = test[0]
		outputs = test[2]
		for output in outputs :
			extension = os.path.splitext(output)[-1]
			base = prefix(datapath, case, output)
			badResult = badResultName(base, extension)
			if os.access(badResult, os.R_OK) :
				failedCases.append(case)
	return failedCases

def accept(datapath, back2BackCases, archSpecific=False, cases=[]) :
	remainingCases = cases[:]
	for test in back2BackCases :
		case = test[0]
		command = test[1]
		outputs = test[2]
		if cases and case not in cases : continue
		if cases : remainingCases.remove(case)
		for output in outputs :

			extension = os.path.splitext(output)[-1]
			base = prefix(datapath, case, output)
			badResult = badResultName(base, extension)
			if not os.access(badResult, os.R_OK) : continue
			print "Accepting", badResult

			expectedFilename = expectedArchName(base, extension) if archSpecific else expectedName(base, extension)

			# if exists, remove old expected (to avoid error #183 renaming on windows -file existent...-)
			if os.path.exists(expectedFilename) : 
				try :
					os.remove(expectedFilename)
				except:
					print "WARNING: cannot remove previously expected file %s" % expectedFilename
					pass

			os.rename(badResult, expectedFilename)

			try:
				os.remove(diffBaseName(base)+extension)
			except: 
				pass
	if remainingCases :
		print "Warning: No such test cases:", ", ".join("'%s'"%case for case in remainingCases)

def removeIfExists(filename) :
	try: os.remove(filename)
	except: pass

def passB2BTests(datapath, back2BackCases, testSuiteName, dry_run, extra_args_for_diff) :
	failedCases = []	
	
	testsuite = TestSuite(testSuiteName)
		

	if dry_run : 
		print "# DATAPATH=%s" % datapath
	for test in back2BackCases : 
		extra_args_for_diff_case = extra_args_for_diff.copy()
		arguments = len(test) 
		if arguments == 3 :
			case, command, outputs = test
		elif arguments == 4 : 
			case, command, outputs, optional_arguments = test
			extra_args_for_diff_case.update(optional_arguments)
			# specific platform arguments (_linux, _mac, _win suffixes)
			platformSuffix = { 'Linux' : '_linux', 'Darwin' : '_mac', 'Windows' : '_win' }[platform.system()]
			extra_args_for_diff_case.update(dict([(item[0][:-len(platformSuffix)], item[1]) for item in optional_arguments.items() if item[0][-len(platformSuffix):] == platformSuffix]))
		else : 
			print "WARNING: skipping bad test %s" % test
			continue
		command = os.path.normcase(command)
		if dry_run : 
			print "\nTest %s :" % case 
			print "\t%s\n" % command
		else :
			testsuite.appendTestCase(passB2BTest(datapath, failedCases, case, command, outputs, extra_args_for_diff_case))

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


def passB2BTest(datapath, failedCases, case, command, outputs, extra_args_for_diff):
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
		difference = diff_files(expected, output, diffbase, extra_args_for_diff)
		#diffbase = diffbase+'.wav'
		diffbase = diffbase + extension

		if not difference:
			print ansiColor.add_green_color(" Passed")
			removeIfExists(diffbase)
			removeIfExists(diffbase+'.png')
			removeIfExists(badResultName(base,extension))
		else:
			print ansiColor.add_red_color(" Failed")
			copyfile(output, badResultName(base,extension)) 
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

To run all the (already) failing tests:
	./back2back --filter_failed

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

To know which are the already failing cases:
	./back2back --list_failed

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
	ansiColor.USE_ANSI_COLORS = enable_colors and ansiColor.supports_color()

	os.access( datapath, os.X_OK ) or die(
		"Datapath at '%s' not available. "%datapath +
		"Check the back 2 back script on information on how to obtain it.")

	availableCases = [test[0] for test in back2BackCases]

	if "--list" in argv :

		for case in availableCases :
			print case
		sys.exit()

	if "--list_failed" in argv : 
		print "Failed cases: "
		for case in listFailedCases(datapath, back2BackCases) :
			print "\t%s" % case
		sys.exit()

	if "--accept" in argv :
		cases = argv[argv.index("--accept")+1:]
		cases or die("Option --accept needs a set of cases to accept.\nAvailable cases:\n"+"\n".join(["\t"+test[0] for test in back2BackCases]))
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

	if "--filter_failed" in argv :
		allcases = list(back2BackCases)
		failed_cases = listFailedCases(datapath, back2BackCases)
		back2BackCases = [case for case in allcases if case[0] in failed_cases ]
		
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

	dry_run = True if "--dry" in argv else False

	# parse diff arguments
	allPossibleDiffArguments = {}
	extraArgsForDiff = {}
	for diffClass in set(diff_class_for_type.values()) :
		allPossibleDiffArguments.update(diffClass().getExtraArgsNameAndTypeDict())
	for argument, arg_type in allPossibleDiffArguments.items() :
		if '--%s' % argument in argv :
			extraArgsForDiff[argument] = arg_type(argv[argv.index('--%s' % argument)+1])

	return passB2BTests(datapath, back2BackCases, testSuiteName, dry_run, extraArgsForDiff)

def runBack2BackProgram(datapath, argv, back2BackCases, testSuiteName="undefined", help=help, enable_colors=True) :
	runBack2BackProgram_returnSuccess(datapath, argv, back2BackCases, testSuiteName, help, enable_colors) or die("Tests not passed") 

def runBack2BackProgram_newApi(datapath, argv, back2BackCases, testSuiteName="undefined", help=help, enable_colors=True) :
	print "argv : ",argv
	extra_args = splitCmdLineArguments(argv)
	print "extra args: ", extra_args
	if extra_args['cmdArgs'] :
		tesdtCasesWithExtraArgs = []
		for test in back2BackCases :
			command = "%s %s" % (test[1], " ".join(extra_args['cmdArgs']))
			tesdtCasesWithExtraArgs.append(tuple([test[0]] + [command] + list(test[2:])))
		back2BackCases = tesdtCasesWithExtraArgs
	runBack2BackProgram_returnSuccess(datapath, extra_args['b2bArgs'], back2BackCases, testSuiteName, help, enable_colors) or die("Tests not passed") 

### End of generic stuff
