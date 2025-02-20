import numpy as np
from ethcolor.formats import *
from ethcolor.palettes import Palette, colors_to_palette, NAME_FORMATS
from typing import Iterable, Any

def oklab_diversity_score(colors: Union[Palette, Iterable[ColorLike]]) -> np.floating[Any]:
	'''
	Compute the diversity score for a set of colors.
	The score is the minimum pairwise distance between colors
	in the OKLAB color space.
	A higher score indicates a more diverse set of colors.

	:param colors: List of colors or a `Palette` object.
	:return: Color diversity score.
	'''
	if type(colors) == Palette:
		colors = np.array(colors.get_color_values(COLOR_FORMATS.OKLAB))
	else:
		assert isinstance(colors, Iterable)
		colors = np.array([
			convert_color(c, detect_format(c), COLOR_FORMATS.OKLAB).get_value()
			for c in colors
		])
	return np.min(
		np.linalg.norm(
			colors[None]-colors[:,None], axis=-1
		)[np.triu_indices(len(colors),1)]
	)
def cblind_score(colors: Union[Palette, Iterable[ColorLike]], cblind_modes: Iterable[np.ndarray[Any, np.dtype[np.floating[Any]]]]=np.eye(3)) -> np.floating[Any]:
	"""
	Compute the colorblind score for a set of colors.
	The score is the average oklab diversity score of the colors
	after simulating a series of colorblind modes.
	A higher score indicates a more colorblind-friendly set of colors.

	:param colors: List of colors.
	:param cblind_modes: Colorblind modes to simulate.
		The modes designate a mixture of the influence of protanopia,
		deuteranopia, and tritanopia with individual weights between 0 and 1.
	:return: Colorblind score.
	"""
	from ethcolor.colorblind import simulate_colorblind
	mode_scores = np.zeros(len(list(cblind_modes)))
	if type(colors) == Palette:
		colors = colors.get_color_values(COLOR_FORMATS.OKLAB)
	else:
		assert isinstance(colors, Iterable)
		colors = [
			convert_color(c, detect_format(c), COLOR_FORMATS.OKLAB)
			for c in colors
		]
	for i_mode, mode in enumerate(cblind_modes):
		sim_colors = [simulate_colorblind(c, *mode) for c in colors]
		mode_scores[i_mode] = oklab_diversity_score(sim_colors)
	return np.mean(mode_scores)
def random_colors(n_total: int, **optim_params) -> list[Color]:
	'''
	Generate a random palette of colors by randomly sampling
	RGB values and optimizing them for diversity and colorblindness.
	If `black` or `white` is set, black or white is added as a contrast color
	only during optimization.
	It will automatically be removed afterward.
	This allows to generate colors, that are clearly visible on a black or
	white background.

	:param n_total: Number of colors in the palette.
	:param optim_params: Parameters for the optimization algorithm
		used to optimize the palette (see `optimize_palette`).
	:return: List of colors.
	'''
	init = [Color(COLOR_FORMATS.rgb, np.random.sample(3)) for _ in range(n_total)]
	mask = [True] * n_total
	result = optimize_palette(
		init,
		mask=mask,
		**optim_params,
	)
	assert type(result) == list
	return result
def optimize_palette(colors: Union[Palette, Iterable[ColorLike]], black=False, white=False, change_weight:float=.1, cblind_weight:float=.5, cblind_modes:Iterable[np.ndarray]=np.eye(3), mask:Union[Iterable[bool],None]=None, out_format:Union[COLOR_FORMATS,None]=None) -> Union[Palette, list[Color]]:
	'''
	Optimize a palette of colors for diversity and colorblindness.

	:param colors: List of colors to optimize.
	:param black: Whether to add black as a contrast color during optimization.
	:param white: Whether to add white as a contrast color during optimization.
	:param change_weight: Weight of the change in color values.
		0 means the change in color values is ignored and only
		the colorblind score is considered.
		1 means the colors cannot change (i.e. no optimization).
	:param cblind_weight: Weight of the colorblind score.
		0 means the colorblind score is ignored and only the
		color diversity is considered.
		1 means the colorblind score is the only factor considered
		and the color diversity is ignored.
	:param cblind_modes: Colorblind modes to simulate.
		The modes designate a mixture of the influence of protanopia,
		deuteranopia, and tritanopia with individual weights between 0 and 1.
	:param mask: Mask for the colors to optimize. This should be a list/array of booleans, where `True` means the color is optimized and `False` means it is kept as is. If `None`, all colors are optimized.
	:param out_format: Output format of the colors. If `None` is specified, uses the detected format of the first input color.
	:return: Optimized palette of colors either as `Palette` iff input was a `Palette` object or as list of `Color`s.
	'''
	if type(colors) == Palette:
		in_palette = colors
		colors = colors.get_color_values()
	else:
		in_palette = None
		assert isinstance(colors, Iterable)
		colors = list(colors)
	mask = np.array([*mask], dtype=bool) if not mask is None else np.ones(len(colors),dtype=bool)
	if out_format is None: out_format = detect_format(colors[0])
	if black:
		colors.append(Color(COLOR_FORMATS.rgb, np.zeros(3)))
		mask = np.array([*mask, False])
	if white:
		colors.append(Color(COLOR_FORMATS.rgb, np.ones(3)))
		mask = np.array([*mask, False])
	from scipy.optimize import minimize
	# Translate to OKLAB color space
	colors = np.array([
		convert_color(c, detect_format(c), COLOR_FORMATS.OKLAB)
		for c in colors
	])
	color_values = np.array([
		c.get_value()
		for c in colors
	])
	def objective(x):
		# Reshape to OKLAB colors
		new_colors = x.reshape(color_values.shape)
		# Translate to RGB to fix out-of-bounds values
		new_colors = np.array([
			convert_color(c, COLOR_FORMATS.OKLAB, COLOR_FORMATS.rgb).get_value()
			for c in new_colors
		])
		new_colors = np.clip(new_colors, 0, 1)
		# Translate back to OKLAB
		new_colors = np.array([
			convert_color(c, COLOR_FORMATS.rgb, COLOR_FORMATS.OKLAB)
			for c in new_colors
		])
		new_color_values = np.array([c.get_value() for c in new_colors])
		new_colors[~mask] = colors[~mask]
		new_color_values[~mask] = color_values[~mask]
		# Compute scores
		new_colors_base_score = oklab_diversity_score(new_colors)
		new_colors_cb_score = cblind_score(new_colors, cblind_modes)
		new_colors_diff_score = np.mean(np.linalg.norm(color_values-new_color_values,axis=-1)**2)
		total_score = (
			change_weight*new_colors_diff_score
			- (1-change_weight) * (
				cblind_weight * new_colors_cb_score
				+ (1-cblind_weight) * new_colors_base_score
			)
		)
		return total_score
	res = minimize(objective, color_values.flatten(), bounds=[
		(0,1) if i==0 else (-.5,.5)
		for _ in range(len(colors))
		for i in range(3)
	]).x.reshape(color_values.shape)
	res = np.array([
		convert_color(c, COLOR_FORMATS.OKLAB, COLOR_FORMATS.rgb).get_value()
		for c in res
	])
	res = np.clip(res, 0, 1)
	res_colors = [convert_color(c, COLOR_FORMATS.rgb, out_format) for c in res]
	if black or white: res_colors = res_colors[:-black-white]
	if in_palette is not None:
		return Palette(in_palette.name, [
			[n, c]
			for n,c in zip(in_palette.get_color_names(), res_colors)
		])
	else: return res_colors
def extend_colors(colors: Union[Palette, Iterable[ColorLike]], n_total: int, n_init_tries: int=10, out_format:Union[COLOR_FORMATS,None]=None, post_optimize:bool=True, cblind_weight:float=.5, cblind_modes:Iterable[np.ndarray]=np.eye(3), black=False, white=False, name_format:NAME_FORMATS=NAME_FORMATS.SNAKE) -> list[Color]:
	'''
	Extends the given palette or list of colors by adding random colors.
	For each color to add, `n_init_tries` random colors are tried and the one
	with the highest diversity and colorblind score is added.
	If `post_optimize` is set, the extended palette is optimized for diversity and colorblindness.
	During the post optimization, the original colors are kept fixed.

	:param colors: List of colors or Palette to extend.
	:param n_total: Number of colors in the extended palette.
	:param n_init_tries: Number of random colors to try for each new color.
	:param out_format: Output format of the colors. If `None` is specified, uses the detected format of the first input color.
	:param post_optimize: Whether to optimize the extended palette.
	:param cblind_weight: See `optimize_palette`.
	:param cblind_modes: See `optimize_palette`.
	:param black: Whether to add black as a contrast color during optimization.
	:param white: Whether to add white as a contrast color during optimization.
	:param name_format: Name format for the new palette (only applies if input was a `Palette` object).
	:return: List of colors if `colors` was a list of colors, an extended `Palette` if `colors` was a `Palette`.
	'''
	if type(colors) == Palette:
		color_values = np.array([
			c.get_value()
			for c in colors.get_color_values(COLOR_FORMATS.OKLAB)
		])
	else:
		assert isinstance(colors, Iterable)
		color_values = np.array([
			convert_color(c, detect_format(c), COLOR_FORMATS.OKLAB).get_value()
			for c in colors
		])
	n_add_colors = n_total - color_values.shape[0]
	if n_add_colors <= 0: return colors
	if black:
		color_values = np.concatenate([
			color_values,
			convert_color(np.zeros(3), COLOR_FORMATS.rgb, COLOR_FORMATS.OKLAB).get_value()[None],
		])
	if white:
		color_values = np.concatenate([
			color_values,
			convert_color(np.ones(3), COLOR_FORMATS.rgb, COLOR_FORMATS.OKLAB).get_value()[None],
		])
	add_colors = np.zeros((n_add_colors,3))
	for icol in range(n_add_colors):
		candidates = np.array([
			convert_color(np.random.sample(3), COLOR_FORMATS.rgb, COLOR_FORMATS.OKLAB).get_value()
			for _ in range(n_init_tries)
		])
		curr_colors = [
			Color(COLOR_FORMATS.OKLAB, v)
			for v in [*color_values, *add_colors[:icol]]
		]
		candidate_scores = np.zeros(n_init_tries)
		for icand in range(n_init_tries):
			candidate = candidates[icand]
			cand_color = Color(COLOR_FORMATS.OKLAB, candidate)
			candidate_scores[icand] = (
				cblind_weight * cblind_score(curr_colors + [cand_color], cblind_modes)
				+ (1-cblind_weight) * oklab_diversity_score(curr_colors + [cand_color])
			)
		add_colors[icol] = candidates[np.argmax(candidate_scores)]
	all_colors = [
		Color(COLOR_FORMATS.OKLAB, v)
		for v in [*color_values, *add_colors]
	]
	if post_optimize:
		all_colors = optimize_palette(
			all_colors,
			change_weight=.01,
			cblind_weight=cblind_weight,
			cblind_modes=cblind_modes,
			mask=[False]*len(color_values) + [True]*n_add_colors,
			out_format=out_format
		)
	else:
		all_colors = [convert_color(c, COLOR_FORMATS.OKLAB, out_format) for c in all_colors]
	if type(colors) == Palette:
		return colors.union(colors_to_palette("tmp", all_colors, name_format=name_format))
	return all_colors[:-n_add_colors-black-white] + all_colors[-n_add_colors:]
def random_incremental_colors(n_total:int, n_start:int=3, n_increment:int=1, n_init_tries:int=10, out_format:Union[COLOR_FORMATS,None]=None, post_optimize:bool=True, cblind_weight:float=.5, cblind_modes:Iterable[np.ndarray]=np.eye(3), black=False, white=False) -> list[Color]:
	'''
	Generate a palette of colors by adding random colors incrementally.
	At first, `n_start` colors are generated with `random_colors`.
	Then, `n_increment` colors are added in each step by optimizing the
	current palette with `extend_colors`.

	:param n_total: Number of colors in the final palette.
	:param n_start: Number of colors to start with.
	:param n_increment: Number of colors to add in each step.
	:param n_init_tries: See `extend_colors`.
	:param out_format: Final format of the generated colors.
	:param post_optimize: See `extend_colors`.
	:param cblind_weight: See `optimize_palette`.
	:param cblind_modes: See `optimize_palette`.
	:param black: See `optimize_palette` or `extend_colors`.
	:param white: See `optimize_palette` or `extend_colors`.
	:return: List of `Color`s.
	'''
	colors = random_colors(n_start, black=black, white=white, cblind_weight=cblind_weight, cblind_modes=cblind_modes, change_weight=.01, out_format=out_format)
	while len(colors) < n_total:
		n_add = min(n_increment, n_total-len(colors))
		colors = extend_colors(colors, len(colors)+n_add, n_init_tries=n_init_tries, out_format=out_format, post_optimize=post_optimize, cblind_weight=cblind_weight, cblind_modes=cblind_modes, black=black, white=white)
	return colors

if 0: # Example
	from ethcolor.util import display_palette
	display_palette(random_colors(8))
