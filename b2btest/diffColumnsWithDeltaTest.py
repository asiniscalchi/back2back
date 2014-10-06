#!/usr/bin/env python

import diffColumnsWithDelta
import os
import sys

def main() :
	test_files_path = os.path.join(os.path.dirname(sys.argv[0]), "testFiles", "diffColumnsWithDelta")
	test_files = [ 
			("test1DiffLinesNrA", "test1DiffLinesNrB"), 
			("test2DiffColumnsNrA", "test2DiffColumnsNrB"), 
			("test3DiffColumnStringContentA", "test3DiffColumnStringContentB"), 
			("test4DiffColumnFloatValueA", "test4DiffColumnFloatValueB"), 
			("test5DiffMixedStringsAndFloatsA", "test5DiffMixedStringsAndFloatsB"), 
			("test6NoDiffA", "test6NoDiffB"), 
		     ]
	for testNr in range(len(test_files)) :
		test = test_files[testNr]
		expectedFilename = os.path.join(test_files_path, test[0])
		resultFilename = os.path.join(test_files_path, test[1])

		print "Executing diff between %s and %s..." % (test[0], test[1])
		errors = diffColumnsWithDelta.differences(expectedFilename, resultFilename, resultFilename[:-1]+"Diff", {})
		if not errors : 
			print "\tFiles are equal!"
		else :
			print "\tFiles diff : "
			print "\t\t",errors
		print "...."


if __name__ == "__main__" :
	main()

