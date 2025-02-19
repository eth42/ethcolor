import numpy as np
from .formats import COLOR_FORMATS, detect_format, convert_color, Color, ColorLike
from .palettes import Palette
from enum import Enum
from typing import Union, Iterable

class INTERPOLATION_SPACES(Enum):
	RGB = 1,
	CIE = 2,
	OKLAB = 3,
	HSV = 4,
	HSL = 5,

def hue_sort(colors: list[ColorLike]) -> list[ColorLike]:
	'''
	Sort colors by hue (H in the HSV color model).

	:param colors: list of colors.
	'''
	return sorted(colors, key=lambda c: convert_color(c, out_format=COLOR_FORMATS.HSV).get_value()[0])
def color_mix(c1: ColorLike, percent: float, c2: ColorLike, out_format:Union[COLOR_FORMATS,None]=None, space:INTERPOLATION_SPACES=INTERPOLATION_SPACES.OKLAB) -> Color:
	'''
	Mix two colors. Works like `c1!percent!c2` TikZ syntax.

	:param c1: First color.
	:param percent: Mixing percentage of the first color (0-100).
	:param c2: Second color.
	:param out_format: Output format of the color. If `None` is specified, uses the detected format of the first input color.
	:param space: Color space to use for interpolation.
	'''
	if out_format is None: out_format = detect_format(c1)
	match space:
		case INTERPOLATION_SPACES.RGB: mid_format = COLOR_FORMATS.rgba
		case INTERPOLATION_SPACES.CIE: mid_format = COLOR_FORMATS.CIEA
		case INTERPOLATION_SPACES.OKLAB: mid_format = COLOR_FORMATS.OKLABA
		case INTERPOLATION_SPACES.HSV: mid_format = COLOR_FORMATS.HSVA
		case INTERPOLATION_SPACES.HSL: mid_format = COLOR_FORMATS.HSLA
		case _: raise ValueError("Unknown color space \"{:}\"".format(space))
	a,b = percent/100,1-percent/100
	c1 = convert_color(c1, detect_format(c1), mid_format).get_value()
	c2 = convert_color(c2, detect_format(c2), mid_format).get_value()
	return convert_color(c1*a+c2*b, mid_format, out_format)
def interpolate_colors(c1: ColorLike, c2: ColorLike, n_steps: int, out_format: Union[COLOR_FORMATS,None]=None, space:INTERPOLATION_SPACES=INTERPOLATION_SPACES.OKLAB) -> list[Color]:
	'''
	Interpolate between two colors. The first and last colors are `c1` and `c2`.
	Colors inbetween are interpolated linearly in the specified color model.

	:param c1: First color.
	:param c2: Second color.
	:param n_steps: Number of steps to interpolate.
	:param out_format: Output format of the color. If `None` is specified, uses the detected format of the first input color.
	:param space: Color space to use for interpolation.
	:return: List of colors.
	'''
	if out_format is None: out_format = detect_format(c1)
	match space:
		case INTERPOLATION_SPACES.RGB: mid_format = COLOR_FORMATS.rgba
		case INTERPOLATION_SPACES.CIE: mid_format = COLOR_FORMATS.CIEA
		case INTERPOLATION_SPACES.OKLAB: mid_format = COLOR_FORMATS.OKLABA
		case INTERPOLATION_SPACES.HSV: mid_format = COLOR_FORMATS.HSVA
		case INTERPOLATION_SPACES.HSL: mid_format = COLOR_FORMATS.HSLA
		case _: raise ValueError("Unknown color space \"{:}\"".format(space))
	c1 = convert_color(c1, detect_format(c1), mid_format).get_value()
	c2 = convert_color(c2, detect_format(c2), mid_format).get_value()
	return [
		convert_color(
			a*c1+(1-a)*c2,
			mid_format,
			out_format
		)
		for a in np.linspace(0,1,n_steps)
	]
def interpolate_color_series(colors: Iterable[ColorLike], n_steps_total: int, out_format: Union[COLOR_FORMATS,None]=None, space:INTERPOLATION_SPACES=INTERPOLATION_SPACES.OKLAB) -> list[Color]:
	'''
	Interpolate between a series of colors. The first and last colors are `colors[0]` and `colors[-1]`.
	Colors inbetween are interpolated linearly in the specified color model
	where spacings between the input colors are uniform.

	:param colors: List of colors.
	:param n_steps_total: Total number of steps to interpolate.
	:param out_format: Output format of the color. If `None` is specified, uses the detected format of the first input color.
	:param space: Color space to use for interpolation.
	:return: List of colors.
	'''
	if out_format is None: out_format = detect_format(colors[0])
	match space:
		case INTERPOLATION_SPACES.RGB: mid_format = COLOR_FORMATS.rgba
		case INTERPOLATION_SPACES.CIE: mid_format = COLOR_FORMATS.CIEA
		case INTERPOLATION_SPACES.OKLAB: mid_format = COLOR_FORMATS.OKLABA
		case INTERPOLATION_SPACES.HSV: mid_format = COLOR_FORMATS.HSVA
		case INTERPOLATION_SPACES.HSL: mid_format = COLOR_FORMATS.HSLA
		case _: raise ValueError("Unknown color space \"{:}\"".format(space))
	colors = np.array([
		convert_color(c, detect_format(c), mid_format).get_value()
		for c in [*colors,colors[-1]]
	])
	positions = np.linspace(0,len(colors)-2,n_steps_total)
	a,b = positions.astype(int),positions%1
	interp_colors = colors[a]*(1-b)[:,None]+colors[a+1]*b[:,None]
	return [convert_color(c, mid_format, out_format) for c in interp_colors]
def create_plotly_scale(colors: Union[Palette, Iterable[ColorLike]], positions=None) -> list[list[Union[float,str]]]:
	'''
	Create a plotly-compatible color scale from a list of colors.
	The resulting list will contain colors in the RGBA string format.

	:param colors: List of colors or `Palette` object.
	:param positions: List of positions for the colors (0-1).
	:return: List of colors in the format [[position, color], ...].
	'''
	if type(colors) == Palette: colors = colors.get_color_values()
	if positions is None: positions = np.linspace(0,1,len(colors))
	return [[p,convert_color(v,out_format=COLOR_FORMATS.RGBA_S).get_value()] for p,v in zip(positions,colors)]
def display_palette(colors: Union[Palette, Iterable[ColorLike]], width: int=500, height: int=80) -> None:
	'''
	Display a list of colors in a horizontal bar.

	:param colors: List of colors or `Palette` object.
	:param width: Width of the display.
	:param height: Height of the display.
	'''
	from PIL import Image
	from IPython.display import display
	if type(colors) == Palette: colors = colors.get_color_values()
	img_arr = np.zeros((height,width,3), dtype=np.uint8)
	x_limits = np.linspace(0,width,len(colors)+1).round().astype(int)
	for i,c in enumerate(colors):
		rgba = convert_color(c, detect_format(c), COLOR_FORMATS.rgba).get_value()
		rgb, alpha = rgba[:3], rgba[3]
		rgb = alpha*rgb+(1-alpha)*np.ones(3)
		rgb = (rgb*255).round().astype(int)
		img_arr[:,x_limits[i]:x_limits[i+1]] = rgb
	display(Image.fromarray(img_arr))

