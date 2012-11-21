#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Copyright 2012 David García Garzón

This file is part of back2back

back2back is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

back2back is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

extensions = [
	'wav',
	'ogg',
	'flac',
	'voc',
	'au',
]

def differences(expected, result, diffBase=None, threshold_dBs=-80, allow_different_duration=False, expected_offset=0, result_offset = 0) :
	import wavefile_audiolab
	import numpy as np
	import math

	mandatory_attributes = [ 
				'samplerate', 
				'channels',
				'frames',
				] 
	if expected_offset> 0 or result_offset > 0 : 
		allow_different_duration = True
	if allow_different_duration : 
		mandatory_attributes.remove('frames')

	errors = []
	with wavefile_audiolab.WaveReader(expected, expected_offset) as expectedReader :
		with wavefile_audiolab.WaveReader(result, result_offset) as resultReader :
			for attribute in mandatory_attributes :
				expectedAttribute = getattr(expectedReader, attribute)
				resultAttribute = getattr(resultReader, attribute)
				if expectedAttribute != resultAttribute :
					errors.append("Expected %s was %s but got %s"%(
						attribute,
						expectedAttribute,
						resultAttribute,
						))
			# Errors detected so far avoid further comparison
			if errors : return errors

			hopsize = 1024
			period = 0
			channels = expectedReader.channels


			class NullWriter(object) :
				def __init__(self) :
					pass
				def __enter__(self) :
					pass
				def __exit__(self, *args ) :
					pass
				def write(self, data) :
					pass

			if diffBase is None :
				diffWriter = NullWriter()
			else :
				import os.path
				extension = os.path.splitext(result)[-1]
				diffwav = diffBase+extension
				diffWriter = wavefile_audiolab.WaveWriter(diffwav, 
						channels = channels,
						samplerate = expectedReader.samplerate,
						)

			with diffWriter :
				resultData = np.zeros((hopsize, channels), np.float64)
				expectedData = np.zeros((hopsize, channels), np.float64)

				maxdiff      = np.zeros((channels))
				maxdiffpos   = np.array([None]*channels)
				nanmiss      = np.array([False]*channels)
				nanmisspos   = np.array([None]*channels)
				pinfmiss     = np.array([False]*channels)
				pinfmisspos  = np.array([None]*channels)
				ninfmiss     = np.array([False]*channels)
				ninfmisspos  = np.array([None]*channels)
				while True :
					actualResultHop = resultReader.read(resultData)
					actualExpectedHop = expectedReader.read(expectedData)
					assert actualExpectedHop == actualExpectedHop, "Unexpected unbalanced hop in file readers"
					if actualExpectedHop == 0 : break # al file read

					resultData = resultData[:actualResultHop]
					expectedData = expectedData[:actualResultHop]

					def check(expected, result, predicate, misses, missesPos) :
						found_expected = predicate(expectedData)
						found_result   = predicate(resultData)
						currentMisses  = (found_expected != found_result)
						if currentMisses.any() :
							cummulativeCompare(misses, missesPos, currentMisses, period*hopsize)
							# remove conflictive values
							conflictive = found_result | found_expected
							resultData[conflictive] = 0
							expectedData[conflictive] = 0

					check(expectedData, resultData, np.isnan, nanmiss, nanmisspos)
					check(expectedData, resultData, np.isposinf, pinfmiss, pinfmisspos)
					check(expectedData, resultData, np.isneginf, ninfmiss, ninfmisspos)

					diffData = resultData - expectedData
					diffWriter.write(diffData)
					cummulativeCompare(maxdiff, maxdiffpos, diffData, period*hopsize)

					period += 1

			threshold_amplitude = 10**(threshold_dBs/20)

			errors += [
				"Value missmatch at channel %i, maximum difference of %f (%0.3fdB) at sample %i, threshold at %f (%0.3fdB)" %
					( channel, value, 20*math.log10(value), sample, threshold_amplitude, threshold_dBs )
					for channel, (value, sample)
					in enumerate(zip(maxdiff, maxdiffpos))
					if value > threshold_amplitude
					] + [
				"Nan missmatch at channel %i, first at sample %i" %
					( channel, sample )
					for channel, (value, sample)
					in enumerate(zip(nanmiss, nanmisspos))
					if value
					] + [
				"Positive infinite missmatch at channel %i, first at sample %i" %
					( channel, sample )
					for channel, (value, sample)
					in enumerate(zip(pinfmiss, pinfmisspos))
					if value
					] + [
				"Negative infinite missmatch at channel %i, first at sample %i" %
					( channel, sample )
					for channel, (value, sample)
					in enumerate(zip(ninfmiss, ninfmisspos))
					if value
					]

			return errors

def hopMax(channels, offset=0) :
	"""Returns values and positions of absolute maximi
	for each channel of a multichannel audio chunk.
	First index of the input matrix should be the position
	and the second index the channel.
	If provided, offset is added to the maximum positions.
	"""
	abschannels = abs(channels)
	return (
		abschannels.max(axis=0),
		abschannels.argmax(axis=0)+offset,
		)

def mergeHopMax(old, oldpos, new, newpos) :
	"""Updates a multichannel maximum tracking structure
	(old, oldpos) with the new maximi (new, newpos)
	of a new chunk of audio.
	Updates the maximum for a channel just if the one
	of the new chunk for that channel is greater.
	The old structure is modified in-place and is returned
	as well for convenience.
	"""
	choser = old < new
	old[choser] = new[choser]
	oldpos[choser] = newpos[choser]
	return (old, oldpos)

def cummulativeCompare(values, pos, diff, offset) :
	"""Given a set of multichannel values (diff)
	updates the multichannel maximi.
	"""
	newvalues, newpos = hopMax(diff, offset)
	values, pos = mergeHopMax(values, pos, newvalues, newpos)
	return values, pos



if __name__ == '__main__' :

	import sys
	diffs = differences(*sys.argv[1:])
	if not diffs : print "Ok"; sys.exit(0)
	for d in diffs :
		print >> sys.stderr, d

	sys.exit(-1)




