from ethcolor.formats import *
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

class NAME_FORMATS(Enum):
	SNAKE = 1,
	CAMEL = 2,
	SPACE = 3,
	SPACE_LOWER = 4,
	NOSPACE = 5,
	NOSPACE_LOWER = 6,

class Palette:
	def __init__(self: 'Palette', name: str, colors: Iterable[Union[tuple[str,ColorLike],Iterable[Union[str,ColorLike]]]]):
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
			colors[i][1] = convert_color(c[1], detect_format(c[1]), COLOR_FORMATS.rgba) # type: ignore
		self.colors = colors
		self.colors_by_name = {c[0]:c[1] for c in colors} # type: ignore
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
	def get_color(self: 'Palette', i: Union[str,int], out_format:COLOR_FORMATS=COLOR_FORMATS.RGBA_S) -> Color:
		'''
		Get a color from the palette.
		The index will "wrap around" if it exceeds the number of colors.
		Thus, for any positive integer `i`, will produce a valid color.

		:param i: Index or name of the color.
		:param out_format: Output format of the color.
		:return: Color in the specified format.
		'''
		if type(i) == str:
			return self.colors[self.colors_by_name[i]] # type: ignore
		return convert_color(self.colors[i%len(self.colors)][1], COLOR_FORMATS.rgba, out_format) # type: ignore
	def get_color_names(self: 'Palette') -> list[str]:
		'''
		Get the names of the colors in the palette.
		This produces the same order as `get_color_values`.

		:return: List of color names.
		'''
		return [c[0] for c in self.colors] # type: ignore
	def get_color_values(self: 'Palette', out_format:COLOR_FORMATS=COLOR_FORMATS.RGBA_S) -> list[Color]:
		'''
		Get the values of the colors in the palette.
		This produces the same order as `get_color_names`.

		:param out_format: Output format of the colors.
		:return: List of color values.
		'''
		return [convert_color(c[1], COLOR_FORMATS.rgba, out_format) for c in self.colors] # type: ignore
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
		self.colors_by_name[name] = self.colors[-1][1] # type: ignore
		return self
	def remove_color(self: 'Palette', name: str) -> 'Palette':
		'''
		Remove a color from the palette.
		Fails with an AssertionError if the color name does not exist.

		:param name: Name of the color.
		:return: Self for daisy chaining.
		'''
		assert name in self.colors_by_name, f"Color name '{name}' not found"
		self.colors = [c for c in self.colors if c[0] != name] # type: ignore
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
				result.add_color(name, color) # type: ignore
			else:
				warnings.warn(f"Color '{name}' already exists in palette '{self.name}', skipping this color")
		return result
	def to_latex(self: 'Palette', prefix_palette_name: Union[str,bool]=True) -> str:
		r'''
		Convert the palette to a block of LaTeX code defining all colors using the `\definecolor` package and using RGB values.
		If `prefix_palette_name` is `True`, the colors are prefixed with the palette name separated with an underscore.
		If `prefix_palette_name` is a string, the colors are prefixed with this string (no implicit underscore!).
		If `prefix_palette_name` is `False`, no prefix is added.

		:param prefix_palette_name: Prefix for the color names.
		:return: LaTeX code defining the colors.
		'''
		prefix = (
			self.name+"_"
			if type(prefix_palette_name) == bool and prefix_palette_name else
			prefix_palette_name
			if type(prefix_palette_name) == str else 
			None
		)
		single_col_template = r"\definecolor{{{:}}}{{RGB}}{{{:},{:},{:}}}"
		color_defs = "\n".join([
			single_col_template.format(
				col_name if prefix is None else f"{prefix}{col_name}",
				*col.get_value(COLOR_FORMATS.RGB) # type: ignore
			)
			for col_name, col in self.colors
		])
		return f"% Palette: {self.name}\n{color_defs}"
	def to_python(self: 'Palette', include_alpha: bool=False) -> str:
		'''
		Convert the palette to a block of Python code defining the `Palette` object.
		This is especially useful if you optimized the palette or created a random palette and want to reuse it in the future.

		:return: Python code defining the palette.
		'''
		color_strings: list[str] = list(map(lambda v: f'"{v}"', self.get_color_values()))
		color_defs = "\n".join([
			f'  ["{name}", "{color.get_value(COLOR_FORMATS.RGBA_S if include_alpha else COLOR_FORMATS.RGB_S)}"],' # type: ignore
			for name, color in self.colors
		])
		return f"# Palette: {self.name}\npalette = ethcolor.Palette(\"{self.name}\", [\n{color_defs}\n])"
	def to_renamed_colors(self: 'Palette', color_name_format: NAME_FORMATS=NAME_FORMATS.SNAKE) -> 'Palette':
		'''
		Create a copy of the palette with automatically renamed colors.

		:return: New palette object.
		'''
		return colors_to_palette(self.name, self.get_color_values(), name_format=color_name_format)

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
	def get_palette(self: 'PaletteManager', name:Union[str, None]=None) -> Palette:
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

def colors_to_palette(palette_name: str, colors: Iterable[ColorLike], color_names:Union[Iterable[str],None]=None, name_format: NAME_FORMATS=NAME_FORMATS.SNAKE) -> Palette:
	'''
	Create a palette from a list of colors using either specified color names or "guessing" the colors using `pycolornames`.

	:param colors: List of colors.
	:param name: Name of the palette.
	:param color_names: List of color names. If `None` is specified, guesses the color names using `pycolornames`.
	:return: Palette object.
	'''
	colors = list(colors)
	if color_names is None:
		import colornames
		color_names = [
			colornames.find(*map(int,convert_color(c, out_format=COLOR_FORMATS.RGB).get_value()))
			for c in colors
		]
		# Append numbers to names occuring more than once
		unique_names, name_counts = np.unique(color_names, return_counts=True)
		reoccuring_name_counts = {
			name: 0
			for name,count in zip(unique_names,name_counts)
			if count > 1
		}
		for i in range(len(color_names)):
			if color_names[i] in reoccuring_name_counts:
				reoccuring_name_counts[color_names[i]] = reoccuring_name_counts[color_names[i]]+1
				color_names[i] = "{:} {:}".format(color_names[i],reoccuring_name_counts[color_names[i]])
		# Simplify names
		match name_format:
			case NAME_FORMATS.SNAKE: color_names = [n.lower().replace(" ","_") for n in color_names]
			case NAME_FORMATS.CAMEL: color_names = [n.title().replace(" ","") for n in color_names]
			case NAME_FORMATS.SPACE: pass
			case NAME_FORMATS.SPACE_LOWER: color_names = [n.lower() for n in color_names]
			case NAME_FORMATS.NOSPACE: color_names = [n.replace(" ","") for n in color_names]
			case NAME_FORMATS.NOSPACE_LOWER: color_names = [n.lower().replace(" ","") for n in color_names]
			case _: raise ValueError("Unknown name format \"{:}\"".format(name_format))
	return Palette(palette_name, [
		[n, c]
		for n,c in zip(color_names,colors)
	])

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

default_palettes.add_palette(colors_to_palette("plotly", [
	'#636EFA',
	'#EF553B',
	'#00CC96',
	'#AB63FA',
	'#FFA15A',
	'#19D3F3',
	'#FF6692',
	'#B6E880',
	'#FF97FF',
	'#FECB52',
]))

default_palettes.add_palette(colors_to_palette("d3", [
	'#1f77b4',
	'#ff7f0e',
	'#2ca02c',
	'#d62728',
	'#9467bd',
	'#8c564b',
	'#e377c2',
	'#7f7f7f',
	'#bcbd22',
	'#17becf',
]))

