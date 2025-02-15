from formats import *

WHITE = "#fff"
BLACK = "#000"
STANDARD_MIXES = [
	["LIGHT", 50, WHITE],
	["MIDLIGHT", 75, WHITE],
	["MIDDARK", 75, BLACK],
	["DARK", 50, BLACK],
]

class Palette:
	def __init__(self, name, colors):
		self.name = name
		# Ensure that colors are in rgba format:
		for i,c in enumerate(colors):
			colors[i][1] = convert_color(c[1], detect_format(c[1]), COLOR_FORMATS.rgba)
		self.colors = colors
		self.colors_by_name = {c[0]:c[1] for c in colors}
	def n_colors(self):
		return len(self.colors)
	def get_color(self, i, out_format=COLOR_FORMATS.RGBA_S):
		if type(i) == str: return self.colors[self.colors_by_name[i]]
		return convert_color(self.colors[i%len(self.colors)][1], COLOR_FORMATS.rgba, out_format)
	def get_color_names(self):
		return [c[0] for c in self.colors]
	def get_color_values(self, out_format=COLOR_FORMATS.RGBA_S):
		return [convert_color(c[1], COLOR_FORMATS.rgba, out_format) for c in self.colors]

class PaletteManager:
	def __init__(self):
		self.palettes = {}
		self.default_palette = None
	def add_palette(self, palette, set_default=False):
		self.palettes[palette.name] = palette
		if self.default_palette is None or set_default:
			self.default_palette = palette.name
	def get_palette(self, name=None):
		if name is None: name = self.default_palette
		if name not in self.palettes:
			raise ValueError("Palette \"{:}\" not found".format(name))
		return self.palettes[name]
	def set_default(self, name):
		if name not in self.palettes:
			raise ValueError("Palette \"{:}\" not found".format(name))
		self.default_palette = name

default_palettes = PaletteManager()

# Taken from:
# Masataka Okabe and Kei Ito, "Color Universal Design (CUD): How to make figures and presentations that are friendly to Colorblind people," 2002.
# https://jfly.uni-koeln.de/color/#pallet
default_palettes.add_palette(Palette("cblind", [
	["black","#000000"],
	["orange","#fba200"],
	["cyan","#00b7ec"],
	["green","#00a177"],
	["yellow","#f6e737"],
	["blue","#0077b8"],
	["vermillion","#f4640d"],
	["purple","#e47ead"],
]))

default_palettes.add_palette(Palette("tudo", [
	['green', '#84b818'],
	['darkgreen', '#649600'],
	['lightgreen', '#e0eacc'],
	['gray', '#cfd0d2'],
	['graybg', '#b2b3cc'],
	['orange', '#e36913'],
	['yellow', '#f2bd00'],
	['citron', '#f9db00'],
	['blue', '#2e86ab'],
	['darkblue', '#1e5972'],
	['violet', '#3d348b'],
	['magenta', '#8b3458'],
	['darkergreen', '#4b622c'],
	['olive', '#53912d'],
	['lime', '#d7d700'],
	['graygreen', '#d9e9e5'],
]))

default_palettes.add_palette(Palette("ml2r", [
	['teal', '#009391'],
	['blue', '#01698c'],
	['orange', '#fab82f'],
	['green', '#80b52c'],
]))

default_palettes.add_palette(Palette("plotly", [
	['plotly0', '#636EFA'],
	['plotly1', '#EF553B'],
	['plotly2', '#00CC96'],
	['plotly3', '#AB63FA'],
	['plotly4', '#FFA15A'],
	['plotly5', '#19D3F3'],
	['plotly6', '#FF6692'],
	['plotly7', '#B6E880'],
	['plotly8', '#FF97FF'],
	['plotly9', '#FECB52'],
]))

default_palettes.add_palette(Palette("d3", [
	['d3_0', '#1f77b4'],
	['d3_1', '#ff7f0e'],
	['d3_2', '#2ca02c'],
	['d3_3', '#d62728'],
	['d3_4', '#9467bd'],
	['d3_5', '#8c564b'],
	['d3_6', '#e377c2'],
	['d3_7', '#7f7f7f'],
	['d3_8', '#bcbd22'],
	['d3_9', '#17becf'],
]))

