import os

class DictionaryLoader():
	"""Abstract Dictionary Loader class."""
	
	def __init__(self):
		pass
		
	def load(self, filename):
		"""Load from file."""
		if not os.path.isfile(filename):
			raise ValueError('Invalid file name: %s' % filename)
		
		return open(filename, 'r').read()

	def write(self, filename, dictionary):
		"""Write to file."""
		filep = open(filename, 'w')
		filep.write(str(dictionary))