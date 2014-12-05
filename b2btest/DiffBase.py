#!/usr/bin/python

class DiffBase(object) : 
	def __init__(self) : 
		self._extraArgsDefaultsDict = {} # for instance, { "threshold_dbs": -80. }
		self._validExtensions = [] # for instance, [ 'txt', 'metadata' ]
	def differences(self, expected, result, diffbase, input_extra_args) :
		print "Not implemented in base class"
		return False
	def getExtraArgsDefaultsDict (self) : 
		return self._extraArgsDefaultsDict.copy()
	def getExtraArgsNameAndTypeDict (self) :
		return dict([(key,type(value)) for key,value in self._extraArgsDefaultsDict.items()])
	def getValidExtensions(self) : 
		return self._validExtensions 
	def getExtraArgsCopyDictUpdated (self, updateDict) : 
		dictToReturn = self._extraArgsDefaultsDict.copy()
		dictToReturn.update(updateDict)
		return dictToReturn

