# Adapted from
# https://github.com/tsarjak/Simulate-Correct-ColorBlindness/blob/master/utils.py

import numpy as np
from enum import Enum
from formats import *

_cb_rgba_to_lmsa_mat = np.array([
	[17.8824, 43.5161, 4.11935, 0],
	[3.45565, 27.1554, 3.86714, 0],
	[0.0299566, 0.184309, 1.46709, 0],
	[0, 0, 0, 1],
]).T
_cb_lmsa_to_rgba_mat = np.linalg.inv(_cb_rgba_to_lmsa_mat)

def _mixed_sim_mat(degree_p=1.0, degree_d=1.0, degree_t=1.0):
	"""
	Matrix for Simulating Hybrid Colorblindness (protanomaly + deuteranomaly + tritanomaly) from LMS color-space.
	:param degree_p: protanomaly degree.
	:param degree_d: deuteranomaly degree.
	:param degree_t: tritanomaly degree.
	"""
	return np.array([
		[1 - degree_p, 2.02344 * degree_p, -2.52581 * degree_p, 0],
		[0.494207 * degree_d, 1 - degree_d, 1.24827 * degree_d, 0],
		[-0.395913 * degree_t, 0.801109 * degree_t, 1 - degree_t, 0],
		[0, 0, 0, 1],
	]).T

def simulate_colorblind(c, protanopia=0.0, deuteranopia=0.0, tritanopia=0.0, out_format=None):
	global _cb_rgba_to_lmsa_mat, _cb_lmsa_to_rgba_mat
	if out_format is None: out_format = detect_format(c)
	rgba = convert_color(c, detect_format(c), COLOR_FORMATS.rgba).get_value()
	lmsa = rgba.dot(_cb_rgba_to_lmsa_mat)
	sim_lmsa = lmsa.dot(_mixed_sim_mat(protanopia, deuteranopia, tritanopia))
	sim_rgba = sim_lmsa.dot(_cb_lmsa_to_rgba_mat)
	sim_rgba = np.clip(sim_rgba, 0, 1)
	return convert_color(sim_rgba, COLOR_FORMATS.rgba, out_format)

if 0: # Example
	from PIL import Image
	from IPython.display import display
	# load test image
	img = Image.open("demo.jpg")
	display(img)

	img_arr = np.array(img)
	from tqdm.auto import tqdm
	with tqdm(total=img_arr.shape[0]*img_arr.shape[1]) as pbar:
		for x in range(img_arr.shape[0]):
			for y in range(img_arr.shape[1]):
				if img_arr[x,y].sum() < 3*255:
					img_arr[x,y] = simulate_colorblind(img_arr[x,y], tritanopia=1.0)
				pbar.update(1)
	display(Image.fromarray(img_arr))
