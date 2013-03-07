#! /usr/bin/python
import os, difflib
from ansi_color import ansiColor

def differences(expected, result, diffbase, extra_args) :
	extension = os.path.splitext(result)[-1]
	difftxt = diffbase+extension

	expectedLines = open(expected, 'U').readlines()
	resultLines = open(result, 'U').readlines()
	diff = list(difflib.unified_diff(expectedLines, resultLines, expected, result))
	open(difftxt, "w").writelines(diff)

	if not diff:
		os.remove(difftxt)
		return []
	return [
		"The result file %s"%(result) + " is different to the expected %s"%(expected),
		]

