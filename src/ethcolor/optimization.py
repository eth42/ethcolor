import numpy as np
from .formats import *
from .palettes import Palette
from typing import Iterable

def oklab_diversity_score(colors: Union[Palette, Iterable[ColorLike]]) -> float:
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
		colors = np.array([
			convert_color(c, detect_format(c), COLOR_FORMATS.OKLAB).get_value()
			for c in colors
		])
	return np.min(
		np.linalg.norm(
			colors[None]-colors[:,None], axis=-1
		)[np.triu_indices(len(colors),1)]
	)
def cblind_score(colors: Union[Palette, Iterable[ColorLike]], cblind_modes: Iterable[np.ndarray]=np.eye(3)) -> float:
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
	from colorblind import simulate_colorblind
	mode_scores = np.zeros(len(cblind_modes))
	if type(colors) == Palette:
		colors = np.array(colors.get_color_values(COLOR_FORMATS.OKLAB))
	else:
		colors = np.array([
			convert_color(c, detect_format(c), COLOR_FORMATS.rgba)
			for c in colors
		])
	for i_mode, mode in enumerate(cblind_modes):
		sim_colors = [simulate_colorblind(c, *mode) for c in colors]
		mode_scores[i_mode] = oklab_diversity_score(sim_colors)
	return np.mean(mode_scores)
def random_colors(n_total: int, **optim_params) -> list[Color]:
	'''
	Generate a random palette of colors by randomly sampling
	RGB values and optimizing them for diversity and colorblindness.

	:param n_total: Number of colors in the palette.
	:param optim_params: Parameters for the optimization algorithm
		used to optimize the palette (see optimize_palette).
	:return: List of colors.
	'''
	init = [Color(COLOR_FORMATS.rgb, np.random.sample(3)) for _ in range(n_total)]
	return optimize_palette(
		init,
		**optim_params,
	)
def optimize_palette(colors: Union[Palette, Iterable[ColorLike]], change_weight:float=.1, cblind_weight:float=.5, cblind_modes:Iterable[np.ndarray]=np.eye(3), out_format:Union[COLOR_FORMATS,None]=None) -> Union[Palette, list[Color]]:
	'''
	Optimize a palette of colors for diversity and colorblindness.

	:param colors: List of colors to optimize.
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
	:param out_format: Output format of the colors. If `None` is specified, uses the detected format of the first input color.
	:return: Optimized palette of colors either as `Palette` iff input was a `Palette` object or as list of `Color`s.
	'''
	if type(colors) == Palette:
		in_palette = colors
		colors = colors.get_color_values()
	else: in_palette = None
	if out_format is None: out_format = detect_format(colors[0])
	from scipy.optimize import minimize
	# Translate to OKLAB color space
	colors = np.array([
		convert_color(c, detect_format(c), COLOR_FORMATS.OKLAB).get_value()
		for c in colors
	])
	def objective(x):
		# Reshape to OKLAB colors
		new_colors = x.reshape(colors.shape)
		# Translate to RGB to fix out-of-bounds values
		new_colors = np.array([
			convert_color(c, COLOR_FORMATS.OKLAB, COLOR_FORMATS.rgb).get_value()
			for c in new_colors
		])
		new_colors = np.clip(new_colors, 0, 1)
		# Translate back to OKLAB
		new_colors = [
			convert_color(c, COLOR_FORMATS.rgb, COLOR_FORMATS.OKLAB)
			for c in new_colors
		]
		new_color_values = np.array([c.get_value() for c in new_colors])
		# Compute scores
		new_colors_base_score = oklab_diversity_score(new_colors)
		new_colors_cb_score = cblind_score(new_colors, cblind_modes)
		new_colors_diff_score = np.mean(np.linalg.norm(colors-new_color_values,axis=-1)**2)
		total_score = (
			change_weight*new_colors_diff_score
			- (1-change_weight) * (
				cblind_weight * new_colors_cb_score
				+ (1-cblind_weight) * new_colors_base_score
			)
		)
		return total_score
	res = minimize(objective, colors.flatten(), bounds=[
		(0,1) if i==0 else (-.5,.5)
		for _ in range(len(colors))
		for i in range(3)
	]).x.reshape(colors.shape)
	res = np.array([
		convert_color(c, COLOR_FORMATS.OKLAB, COLOR_FORMATS.rgb).get_value()
		for c in res
	])
	res = np.clip(res, 0, 1)
	res_colors = [convert_color(c, COLOR_FORMATS.rgb, out_format) for c in res]
	if in_palette is not None:
		return Palette(in_palette.name, [
			[n, c]
			for n,c in zip(in_palette.get_color_names(), res_colors)
		])
	else: return res_colors
def extend_colors(colors: Iterable[ColorLike], n_total: int, out_format:Union[COLOR_FORMATS,None]=None, post_optimize:bool=True, **optimize_kwargs) -> list[Color]:
	'''
	Attempts to automatically extend an existing palette of colors
	to a larger palette by fitting a linear model to the colors
	in OKLAB color space and oversampling along the dominant direction.

	:param colors: List of colors to extend.
	:param n_total: Number of colors in the extended palette.
	:param out_format: Output format of the colors. If `None` is specified, uses the detected format of the first input color.
	:param post_optimize: Whether to optimize the extended palette.
	:param optimize_kwargs: Parameters for the optimization algorithm
		used to optimize the palette (see optimize_palette).
	:return: List of colors.
	'''
	if out_format is None: out_format = detect_format(colors[0])
	colors = np.array([
		convert_color(c, detect_format(c), COLOR_FORMATS.OKLAB).get_value()
		for c in colors
	])
	# Fit linear model into palette
	mean = np.mean(colors,axis=0)
	cov = np.cov(colors,rowvar=False)
	eigvals, eigvecs = np.linalg.eigh(cov)
	eigvecs = eigvecs[np.argsort(eigvals)[::-1]].T
	eigvals = np.sort(eigvals)[::-1]
	dominant_direction = eigvecs[0]
	# Extend palette
	new_colors = np.zeros((n_total-len(colors),3))
	current_positions = (colors-mean).dot(dominant_direction)
	# Find minimum and maximum positions
	max_vals = np.array([1,.5,.5])
	min_vals = np.array([0,-.5,-.5])
	lo,hi=0,1e3
	while abs(hi-lo) > 1e-5:
		mid = (lo+hi)/2
		if np.all(
			(mean+dominant_direction*mid <= max_vals)
			& (mean+dominant_direction*mid >= min_vals)
		): lo = mid
		else: hi = mid
	max_pos = lo
	lo,hi=0,-1e3
	while abs(hi-lo) > 1e-5:
		mid = (lo+hi)/2
		if np.all(
			(mean+dominant_direction*mid <= max_vals)
			& (mean+dominant_direction*mid >= min_vals)
		): lo = mid
		else: hi = mid
	min_pos = lo
	pos_range = max_pos-min_pos
	def target(v):
		w = np.sort([*current_positions,*v])
		return np.sum(np.square(w[1:]-w[:-1]))
	from scipy.optimize import minimize
	new_positions = minimize(
		target,
		np.random.sample(len(new_colors))*pos_range+min_pos,
		bounds=[(min_pos,max_pos) for _ in range(len(new_colors))]
	).x
	new_colors += mean
	new_colors += new_positions[:,None]*dominant_direction[None]
	# new_colors += np.random.multivariate_normal(
	# 	np.zeros(3),
	# 	np.sum([np.outer(vec,vec)*val for vec,val in zip(eigvecs[1:],eigvals[1:])],axis=0),
	# 	len(new_colors)
	# )
	new_colors[:,0] = np.clip(new_colors[:,0], 0, 1)
	new_colors[:,1] = np.clip(new_colors[:,1], -.5, .5)
	new_colors[:,2] = np.clip(new_colors[:,2], -.5, .5)
	result = np.concatenate([colors,new_colors])
	result = [convert_color(c, COLOR_FORMATS.OKLAB, out_format) for c in result]
	if post_optimize: result = optimize_palette(result, **optimize_kwargs)
	return result

if 0: # Example
	from util import display_palette
	display_palette(random_colors(8))
