#!/usr/bin/python

import sys,os


class AnsiColor() :
	def __init__(self) :
		USE_ANSI_COLORS = self.supports_color()
	def supports_color(self):
	    """
	Returns True if the running system's terminal supports color, and False
	otherwise.
	"""
	# copied from django: https://github.com/django/django/blob/master/django/core/management/color.py
	    plat = sys.platform
	    supported_platform = plat != 'Pocket PC' and (plat != 'win32' or
							  'ANSICON' in os.environ)
	    # isatty is not always implemented, #6223.
	    is_a_tty = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
	    if not supported_platform or not is_a_tty:
		return False
	    return True

	def add_ansi_color(self, string, color_code_of_line, color_code_after_line=0) :
		if not self.USE_ANSI_COLORS : return string
		return "\033[%im%s\033[%im" % (color_code_of_line, string, color_code_after_line
		)
	def add_red_color(self, string) :
		return self.add_ansi_color(string, 31, 0)

	def add_green_color(self, string) :
		return self.add_ansi_color(string, 32, 0)

	def add_brown_color (self, string) :
		return self.add_ansi_color(string, 33, 0)

ansiColor = AnsiColor()
