from .formats import *
import warnings
from typing import Iterable

WHITE = "#fff"
BLACK = "#000"
STANDARD_MIXES = [
	["LIGHT", 50, WHITE],
	["MIDLIGHT", 75, WHITE],
	["MIDDARK", 75, BLACK],
	["DARK", 50, BLACK],
]

class Palette:
	def __init__(self: 'Palette', name: str, colors: Iterable[tuple[str,ColorLike]]):
		'''
		Create a new palette.

		:param name: Name of the palette.
		:param colors: List of colors in the format [[color name, color], ...].
		'''
		self.name = name
		# Translate colors to list-of-list format
		colors = list(map(list,colors))
		# Ensure that colors are in rgba format:
		for i,c in enumerate(colors):
			colors[i][1] = convert_color(c[1], detect_format(c[1]), COLOR_FORMATS.rgba)
		self.colors = colors
		self.colors_by_name = {c[0]:c[1] for c in colors}
	def get_name(self: 'Palette') -> str:
		'''
		Get the name of the palette.

		:return: Name of the palette.
		'''
		return self.name
	def n_colors(self: 'Palette') -> int:
		'''
		Get the number of colors in the palette.

		:return: Number of colors.
		'''
		return len(self.colors)
	def get_color(self: 'Palette', i: int, out_format:COLOR_FORMATS=COLOR_FORMATS.RGBA_S) -> Color:
		'''
		Get a color from the palette.
		The index will "wrap around" if it exceeds the number of colors.
		Thus, for any positive integer `i`, will produce a valid color.

		:param i: Index or name of the color.
		:param out_format: Output format of the color.
		:return: Color in the specified format.
		'''
		if type(i) == str: return self.colors[self.colors_by_name[i]]
		return convert_color(self.colors[i%len(self.colors)][1], COLOR_FORMATS.rgba, out_format)
	def get_color_names(self: 'Palette') -> list[str]:
		'''
		Get the names of the colors in the palette.
		This produces the same order as `get_color_values`.

		:return: List of color names.
		'''
		return [c[0] for c in self.colors]
	def get_color_values(self: 'Palette', out_format:COLOR_FORMATS=COLOR_FORMATS.RGBA_S) -> list[Color]:
		'''
		Get the values of the colors in the palette.
		This produces the same order as `get_color_names`.

		:param out_format: Output format of the colors.
		:return: List of color values.
		'''
		return [convert_color(c[1], COLOR_FORMATS.rgba, out_format) for c in self.colors]
	def add_color(self: 'Palette', name: str, color: ColorLike, format:Union[COLOR_FORMATS,None]=None) -> 'Palette':
		'''
		Add a color to the palette.
		Fails with an AssertionError if the color name already exists.

		:param name: Name of the color.
		:param color: Color value.
		:param format: Format of the color value, if `None`, the default heuristic for guessing the color format is applied.
		:return: Self for daisy chaining.
		'''
		assert name not in self.colors_by_name, f"Color name '{name}' already exists"
		self.colors.append([name, convert_color(color, detect_format(color) if format is None else format, COLOR_FORMATS.rgba)])
		self.colors_by_name[name] = self.colors[-1][1]
		return self
	def remove_color(self: 'Palette', name: str) -> 'Palette':
		'''
		Remove a color from the palette.
		Fails with an AssertionError if the color name does not exist.

		:param name: Name of the color.
		:return: Self for daisy chaining.
		'''
		assert name in self.colors_by_name, f"Color name '{name}' not found"
		self.colors = [c for c in self.colors if c[0] != name]
		del self.colors_by_name[name]
		return self
	def ensure_black_and_white(self: 'Palette') -> 'Palette':
		'''
		Ensure that the colors "black" and "white" (with exactly these names) are present in the palette.

		:return: Self for daisy chaining.
		'''
		if "black" not in self.colors_by_name:
			self.add_color("black", BLACK)
		if "white" not in self.colors_by_name:
			self.add_color("white", WHITE)
		return self
	def union(self: 'Palette', other_palette: 'Palette') -> 'Palette':
		'''
		Union with another palette.
		Colors from the other palette are added to a copy of the current palette.
		The current palette object is *not* modified, you must use the return value of this function.
		If a color already exists, a warning is issued and the color is skipped.

		:param other_palette: Palette to union with.
		:return: New palette with the union of the colors.
		'''
		result = Palette(self.name, self.colors)
		for name, color in other_palette.colors:
			if name not in result.colors_by_name:
				result.add_color(name, color)
			else:
				warnings.warn(f"Color '{name}' already exists in palette '{self.name}', skipping this color")
		return result

class PaletteManager:
	def __init__(self: 'PaletteManager'):
		'''
		Create a new empty palette manager.
		'''
		self.palettes = {}
		self.default_palette = None
	def add_palette(self: 'PaletteManager', palette: Palette, set_default: bool=False) -> 'PaletteManager':
		'''
		Add a palette to the manager.
		If `set_default` is `True`, the added palette becomes the new default palette.
		If the palette manager has been empty before, the new palette is always set as the default.

		:param palette: Palette to add.
		:param set_default: Whether to set the added palette as the default.
		:return: Self for daisy chaining.
		'''
		self.palettes[palette.name] = palette
		if self.default_palette is None or set_default:
			self.default_palette = palette.name
		return self
	def get_palette(self: 'PaletteManager', name: str=None) -> Palette:
		'''
		Get a palette from the manager by name.
		If `name` is `None`, the default palette is returned.
		Fails with a ValueError if the palette does not exist.

		:param name: Name of the palette.
		:return: Palette object.
		'''
		if name is None: name = self.default_palette
		if name not in self.palettes:
			raise ValueError("Palette \"{:}\" not found".format(name))
		return self.palettes[name]
	def get_palette_names(self: 'PaletteManager') -> list[str]:
		'''
		Get the names of all palettes in the manager.

		:return: List of palette names sorted alphabetically.
		'''
		return sorted(list(self.palettes.keys()))
	def remove_palette(self: 'PaletteManager', name: str) -> 'PaletteManager':
		'''
		Remove a palette from the manager.
		Fails with a ValueError if the palette does not exist.
		If the default palette is removed, the palette with the alphabetically smallest name in the manager is set as the new default.

		:param name: Name of the palette.
		:return: Self for daisy chaining.
		'''
		if name not in self.palettes:
			raise ValueError("Palette \"{:}\" not found".format(name))
		del self.palettes[name]
		if self.default_palette == name:
			self.default_palette = sorted(list(self.palettes.keys()))[0] if len(self.palettes) > 0 else None
		return self
	def set_default(self: 'PaletteManager', name: str) -> 'PaletteManager':
		'''
		Set the default palette.
		Fails with a ValueError if the palette does not exist.

		:param name: Name of the palette.
		:return: Self for daisy chaining.
		'''
		if name not in self.palettes:
			raise ValueError("Palette \"{:}\" not found".format(name))
		self.default_palette = name
		return self

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

