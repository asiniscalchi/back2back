
from b2btest import setTestSuiteName, runBack2BackProgram_returnSuccess

class B2BTestSuite() :
	def __init__(self, name, datapath) :
		self._name = name
		self._datapath = datapath
		self._back2BackTestCases = []

	def addTestCase(self, name, command, outputs) :
		if isinstance(outputs, str) :
			self._back2BackTestCases.append( (name, command, [outputs]) )
		else :
			self._back2BackTestCases.append( (name, command, outputs) )

	def run(self, argv) :
		setTestSuiteName(self._name)
		runBack2BackProgram_returnSuccess(self._datapath, argv, self._back2BackTestCases)


