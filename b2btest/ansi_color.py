
class AnsiColor() :
	def __init__(self) :
		USE_ANSI_COLORS = True

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
