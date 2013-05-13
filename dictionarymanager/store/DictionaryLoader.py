import os

class DictionaryLoader():
	"""Abstract Dictionary Loader class."""
	
	def __init__(self):
		pass
		
	def load(self, filename):
		"""Load from file."""
		if not os.path.isfile(filename):
			raise ValueError('Invalid file name: %s' % filename)
		
		content = open(filename, 'r').read()
		if "\r\n" in content:
			newline = "\r\n"
		elif "\r" in content:
			newline = "\r"
		else:
			newline = "\n"
		return (content, {"newline": newline})
		

	def write(self, filename, dictionary, conf = None):
		"""Write to file."""
		conf = conf if conf is not None else {}
		filep = open(filename, 'w')
		s = str(dictionary)
		if os.linesep != conf.get("newline"):
			s = s.replace(os.linesep, conf.get("newline"))
		filep.write(s)
