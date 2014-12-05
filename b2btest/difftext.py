#! /usr/bin/python
import os, difflib
from ansi_color import ansiColor
from DiffBase import DiffBase 

class DiffText(DiffBase) : 
	def __init__(self) : 
		DiffBase.__init__(self)
		#self._extraArgsDefaultsDict.update({})
		self._validExtensions = [ 'txt' ]

	def differences(self, expected, result, diffbase, input_extra_args) :
		extra_args = self.getExtraArgsCopyDictUpdated(input_extra_args)
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

