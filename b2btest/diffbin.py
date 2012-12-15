
#! /usr/bin/python
import os
from ansi_color import ansiColor


cmd="hexdump %(expected)s > /tmp/$(basename %(expected)s).hexdump && hexdump %(result)s /tmp/$(basename %(result)s).hexdump && diff /tmp/"

def differences(expected, result, diffbase) :
	expected_basename = os.path.basename(expected)
	result_basename = os.path.basename(result)
	expected_hexdump = os.path.join("/tmp", expected_basename)
	result_hexdump = os.path.join("/tmp", result_basename)
	ok = os.system("hexdump %s > %s" % (expected_basename, expected_hexdump)) == 0
	ok &= os.system("hexdump %s > %s" % (result_basename, result_hexdump)) == 0
	extension = os.path.splitext(result)[-1]
	difftxt = diffbase+extension+".hexdump"

	are_equal = os.system("diff %s %s > %s" % (expected_hexdump if ok else expected, result_hexdump if ok else result, difftxt) ) == 0
	if are_equal: 
		os.system("rm %s" % difftxt)
		return []
	return [
		"The result file %s"%(result) + " is different to the expected %s"%(expected),
		]
