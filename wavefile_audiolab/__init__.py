#!/usr/bin/python
import numpy as np
from scikits.audiolab import Sndfile, available_file_formats, available_encodings, Format


"""
class WaveMetadata(object) :
	strings = [
		'title',
		'copyright',
		'software',
		'artist',
		'comment',
		'date',
		'album',
		'license',
		'tracknumber',
		'genre',
	]
	__slots__ = strings + [
		'_sndfile',
		]

	def __init__(self, sndfile) :
		self._sndfile = sndfile

	def __dir__(self) :
		return self.strings

	def __getattr__(self, name) :
		if name not in self.strings :
			raise AttributeError(name)
		stringid = self.strings.index(name)
		return _lib.sf_get_string(self._sndfile, stringid)

	def __setattr__(self, name, value) :
		if name not in self.strings :
			return object.__setattr__(self, name, value)

		stringid = self.strings.index(name)
		error = _lib.sf_set_string(self._sndfile, stringid, value)
		if error : print ValueError(
			self.strings[stringid],
			error, _lib.sf_error_number(error))
"""

class WaveWriter(object) :
	def __init__(self,
				filename,
				samplerate = 44100,
				channels = 1,
				format = Format('wav','float32'),
				) :

		self._info = {	'filename' : filename , 
				'samplerate' : samplerate,
				'channels' : channels,
				'format' : format,
				'frames' : 0,
				} # TODO: metadata not implemented

		self._sndfile = Sndfile(filename, 'w', format, channels, samplerate)
		if not self._sndfile :
			raise NameError('Sndfile error loading file %s' % filename)

	def __enter__(self) :
		return self
	def __exit__(self, type, value, traceback) :
		self._sndfile.sync()
		self._sndfile.close()
		if value: raise # ????

	def write(self, data) :
		nframes, channels = data.shape
		assert channels == self._info['channels']
		self._sndfile.write_frames(data)

class WaveReader(object) :
	def __init__(self,
				filename,
				samplerate = 0,
				channels = 0,
				file_format = 0,
				offset = 0,
				) :
		sndfile_handler = Sndfile (filename, 'r') 
		if not sndfile_handler :
			raise NameError('Sndfile error loading file %s' % filename)
		self._sndfile = sndfile_handler
		self._info = {	'filename' : filename , 
				'samplerate' : sndfile_handler.samplerate,
				'channels' : sndfile_handler.channels,
				'format' : sndfile_handler.format,
				'frames' : sndfile_handler.nframes,
				} # TODO: metadata not implemented
		self._readed_frames = 0
		if offset > 0 : 
			self.read(np.zeros((offset,self._info['channels']), np.float64))

	def __enter__(self) :
		return self
	def __exit__(self,type,value,traceback) :
		self._sndfile.close()
		if value: raise # ???
	@property
	def channels(self) : return self._info['channels']
	@property
	def format(self) : return self._info['format']
	@property
	def samplerate(self) : return self._info['samplerate']
	@property
	def frames(self) : return self._info['frames']

	def read(self, data) :
		assert data.shape[1] == self.channels
		desired_read_length = data.shape[0] 
		to_read_length = desired_read_length if self._readed_frames + desired_read_length <= self._info['frames'] else self._info['frames'] - self._readed_frames
		tmp_data = self._sndfile.read_frames(to_read_length, dtype=data.dtype)
		for i in range(len(tmp_data)):
			data[i] = tmp_data[i]
		self._readed_frames += to_read_length
#		print data
		return to_read_length

if __name__ == '__main__' :

	with WaveWriter('lala.ogg', channels=2, format=Format('ogg','vorbis')) as w :
		# TODO: Metadata is not working!
		#w.metadata.title = "La casa perdida"
		#w.metadata.artist = "Me"
		data = np.zeros((512,2), np.float32)
		for x in xrange(100) :
			data[:,0] = (x*np.arange(512, dtype=np.float32)%512/512)
			data[512-x:,1] =  1
			data[:512-x,1] = -1
			w.write(data)

	import sys
	import pyaudio
	p = pyaudio.PyAudio()
	with WaveReader('MamaLadilla-TuBar.ogg', channels=2) as r :
		# open stream
		stream = p.open(
				format = pyaudio.paFloat32,
				channels = r.channels,
				rate = r.samplerate,
				frames_per_buffer = 512,
				output = True)
		with WaveWriter('Elvis-float.wav', channels=r.channels, samplerate=r.samplerate) as w :
			data = np.zeros((512,r.channels), np.float32)
			nframes = r.read(data)
			#print "Title:", r.metadata.title
			#print "Artist:", r.metadata.artist
			print "Channels:", r.channels
			print "Format: 0x%x"%r.format
			print "Sample Rate:", r.samplerate
			while nframes :
				sys.stdout.write(".")
				sys.stdout.flush()
				stream.write(data[:nframes,:], nframes)
				w.write(data[:nframes]*.8)
				nframes = r.read(data)
	stream.close()





