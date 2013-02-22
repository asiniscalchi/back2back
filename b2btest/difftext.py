#! /usr/bin/python
import os
from ansi_color import ansiColor

def differences(expected, result, diffbase, extra_args) :
	extension = os.path.splitext(result)[-1]
	difftxt = diffbase+extension
	are_equal = os.system("diff %s %s > %s" % (expected, result, difftxt) ) == 0
	if are_equal: 
		os.system("rm %s" % difftxt)
		return []
	return [
		"The result file %s"%(result) + " is different to the expected %s"%(expected),
		]

