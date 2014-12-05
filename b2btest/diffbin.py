#! /usr/bin/python
import os
from ansi_color import ansiColor
from DiffBase import DiffBase


#cmd="hexdump %(expected)s > /tmp/$(basename %(expected)s).hexdump && hexdump %(result)s /tmp/$(basename %(result)s).hexdump && diff /tmp/"

class DiffBin(DiffBase) : 
	def __init__(self) : 
		DiffBase.__init__(self)
		#self._extraArgsDefaultsDict.update({})
		self._validExtensions = [ 'exe', 'com' ]
	def differences(self, expected, result, diffbase, input_extra_args) :
		extra_args = self.getExtraArgsCopyDictUpdated(input_extra_args)
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
