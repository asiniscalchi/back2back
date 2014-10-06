#!/usr/bin/python
import os

extensions = [
	'prm',
	'atmos',
]

def differences(expected, result, diffbase, extra_args) :
	delta = abs(1E-5 if not extra_args.has_key("delta") else extra_args["delta"])
	extension = os.path.splitext(result)[-1]
	difftxt = diffbase+extension
	expectedLines = open(expected, 'U').readlines()
	resultLines = open(result, 'U').readlines()

	if len(expectedLines) != len(resultLines) : 
		return [
			"Lines mismatch between result file %s (%i lines) and expected file %s (%i lines) " % (result, len(resultLines), expected, len(expectedLines)) ,
			]
	max_value_error = (-1, -1, -1, -1, -1) # (line, column, absValueOfDiff, expectedValue, resultValue)
	strings_errors = []
	for lineNr in range(len(expectedLines)) :
		expectedLine = expectedLines[lineNr].strip().split()
		resultLine = resultLines[lineNr].strip().split()
		if expectedLine == resultLine : 
			continue
		if len(expectedLine) != len(resultLine) :
			return [ "Columns number mismatch between result file %s (%i columns) and expected file %s (%i columns) on line %i"
				% (result, len(resultLine), expected, len(expectedLine), lineNr + 1) ,
			       ]
		for columnNr in range(len(expectedLine)) : 
			expectedColumn = expectedLine[columnNr]
			resultColumn = resultLine[columnNr]
			if expectedColumn == resultColumn : 
				continue
			try : 
				expectedColumnValue = float(expectedColumn)
				resultColumnValue = float(resultColumn)
			except :
				strings_errors += [ " String difference at line %i, column %i. Expected is : \"%s\", result is : \"%s\"\n" % (lineNr + 1, columnNr, expectedColumn, resultColumn),  ]
				continue
			absError = abs(expectedColumnValue - resultColumnValue)
			if  absError < delta or absError <= max_value_error[2] :
				continue
			max_value_error = (lineNr+1, columnNr, absError, expectedColumnValue, resultColumnValue)
	
	if max_value_error == (-1,-1,-1,-1,-1) and not strings_errors : # no error ocurred
		if os.path.exists(difftxt) :
			try: 
				os.remove(difftxt)
			except :
				print "WARNING: there were no differences between the files, but a diff file %s already exists and cannot be removed!" % difftxt
		return []
	if max_value_error != (-1,-1,-1,-1,-1) :
		strings_errors += [ "Max (abs) value diff of %f found on line %i, column %i. Expected was: %f, result is %f.\n" % (max_value_error[2], max_value_error[0], max_value_error[1], max_value_error[3], max_value_error[4]),]
			
	open(difftxt, "w").writelines(strings_errors)
	return [
		"The result file %s"%(result) + " is different to the expected %s"%(expected)
		] + strings_errors
