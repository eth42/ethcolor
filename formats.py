from enum import Enum
import numpy as np

_rgb_to_cie_mat = np.array([
	[0.4124564, 0.3575761, 0.1804375],
	[0.2126729, 0.7151522, 0.0721750],
	[0.0193339, 0.1191920, 0.9503041]
])
_cie_to_rgb_mat = np.array([
	[ 3.2404542, -1.5371385, -0.4985314],
	[-0.9692660,  1.8760108,  0.0415560],
	[ 0.0556434, -0.2040259,  1.0572252]
])
_oklab_to_lms_mat = np.array([
	[1,  0.3963377774,  0.2158037573],
	[1, -0.1055613458, -0.0638541728],
	[1, -0.0894841775, -1.2914855480],
])
_lms_to_cie_mat = np.array([
	[ 1.2270138511, -0.5577999807,  0.2812561490],
	[-0.0405801784,  1.1122568696, -0.0716766787],
	[-0.0763812845, -0.4214819784,  1.5861632204],
])
_cie_to_lms_mat = np.array([
	[0.8189330101, 0.3618667424, -0.1288597137],
	[0.0329845436, 0.9293118715, 0.0361456387],
	[0.0482003018, 0.2643662691, 0.6338517070]
])
_lms_to_oklab_mat = np.array([
	[0.2104542553, 0.7936177850, -0.0040720468],
	[1.9779984951, -2.4285922050, 0.4505937099],
	[0.0259040371, 0.7827717662, -0.8086757660]
])

class COLOR_FORMATS(Enum):
	RGB = 1
	RGBA = 2
	RGB_S = 3
	RGBA_S = 4
	rgb = 5
	rgba = 6
	rgb_S = 7
	rgba_S = 8
	HEX = 9
	CIE = 10
	CIEA = 11
	LMS = 12
	LMSA = 13
	OKLAB = 14
	OKLABA = 15
	HSL = 16
	HSLA = 17
	HSV = 18
	HSVA = 19

class Color:
	def __init__(self, format, value):
		self.format = format
		self.value = value
	def get_value(self, out_format=None):
		if out_format is None: return self.value
		return convert_color(self.value, self.format, out_format).value
	def get_format(self):
		return self.format
	def __repr__(self):
		return f"<{self.format.name}: {self.value}>"
	def __str__(self):
		return convert_color(self, out_format=COLOR_FORMATS.RGBA_S).value

def detect_format(c):
	if type(c) == Color: return c.get_format()
	if type(c) == str:
		if c[0] == "#": return COLOR_FORMATS.HEX
		if c[:4] == "RGB(": return COLOR_FORMATS.RGB_S
		if c[:5] == "RGBA(": return COLOR_FORMATS.RGBA_S
		if c[:4] == "rgb(": return COLOR_FORMATS.rgb_S
		if c[:5] == "rgba(": return COLOR_FORMATS.rgba_S
	if type(c) == np.ndarray:
		if c.dtype in [np.float16, np.float32, np.float64]:
			if len(c) == 3: return COLOR_FORMATS.rgb
			if len(c) == 4: return COLOR_FORMATS.rgba
		else:
			if len(c) == 3: return COLOR_FORMATS.RGB
			if len(c) == 4: return COLOR_FORMATS.RGBA
	raise ValueError("Cannot detect color format for \"{:}\"".format(c))
def convert_color(c, from_format=None, out_format=COLOR_FORMATS.rgba):
	if from_format is None: from_format = detect_format(c)
	if type(c) == Color: c = c.get_value()
	# Move to standardized format
	match from_format:
		case COLOR_FORMATS.RGB: c = _convert_RGB_to_rgba(c)
		case COLOR_FORMATS.RGBA: c = _convert_RGBA_to_rgba(c)
		case COLOR_FORMATS.RGB_S: c = _convert_RGB_S_to_rgba(c)
		case COLOR_FORMATS.RGBA_S: c = _convert_RGBA_S_to_rgba(c)
		case COLOR_FORMATS.rgb: c = _convert_rgb_to_rgba(c)
		case COLOR_FORMATS.rgba: c = _convert_rgba_to_rgba(c)
		case COLOR_FORMATS.rgb_S: c = _convert_rgb_S_to_rgba(c)
		case COLOR_FORMATS.rgba_S: c = _convert_rgba_S_to_rgba(c)
		case COLOR_FORMATS.HEX: c = _convert_hex_to_rgba(c)
		case COLOR_FORMATS.CIE: c = _convert_cie_to_rgba(c)
		case COLOR_FORMATS.CIEA: c = _convert_ciea_to_rgba(c)
		case COLOR_FORMATS.LMS: c = _convert_lms_to_rgba(c)
		case COLOR_FORMATS.LMSA: c = _convert_lmsa_to_rgba(c)
		case COLOR_FORMATS.OKLAB: c = _convert_oklab_to_rgba(c)
		case COLOR_FORMATS.OKLABA: c = _convert_oklaba_to_rgba(c)
		case COLOR_FORMATS.HSL: c = _convert_hsl_to_rgba(c)
		case COLOR_FORMATS.HSLA: c = _convert_hsla_to_rgba(c)
		case COLOR_FORMATS.HSV: c = _convert_hsv_to_rgba(c)
		case COLOR_FORMATS.HSVA: c = _convert_hsva_to_rgba(c)
		case _: raise ValueError("Unknown color format \"{:}\"".format(from_format))
	# Move to target format
	match out_format:
		case COLOR_FORMATS.RGB: result = _convert_rgba_to_RGB(c)
		case COLOR_FORMATS.RGBA: result = _convert_rgba_to_RGBA(c)
		case COLOR_FORMATS.RGB_S: result = _convert_rgba_to_RGB_S(c)
		case COLOR_FORMATS.RGBA_S: result = _convert_rgba_to_RGBA_S(c)
		case COLOR_FORMATS.rgb: result = _convert_rgba_to_rgb(c)
		case COLOR_FORMATS.rgba: result = _convert_rgba_to_rgba(c)
		case COLOR_FORMATS.rgb_S: result = _convert_rgba_to_rgb_S(c)
		case COLOR_FORMATS.rgba_S: result = _convert_rgba_to_rgba_S(c)
		case COLOR_FORMATS.HEX: result = _convert_rgba_to_hex(c)
		case COLOR_FORMATS.CIE: result = _convert_rgba_to_cie(c)
		case COLOR_FORMATS.CIEA: result = _convert_rgba_to_ciea(c)
		case COLOR_FORMATS.LMS: result = _convert_rgba_to_lms(c)
		case COLOR_FORMATS.LMSA: result = _convert_rgba_to_lmsa(c)
		case COLOR_FORMATS.OKLAB: result = _convert_rgba_to_oklab(c)
		case COLOR_FORMATS.OKLABA: result = _convert_rgba_to_oklaba(c)
		case COLOR_FORMATS.HSL: result = _convert_rgba_to_hsl(c)
		case COLOR_FORMATS.HSLA: result = _convert_rgba_to_hsla(c)
		case COLOR_FORMATS.HSV: result = _convert_rgba_to_hsv(c)
		case COLOR_FORMATS.HSVA: result = _convert_rgba_to_hsva(c)
		case _: raise ValueError("Unknown color format \"{:}\"".format(out_format))
	return Color(out_format, result)

def _convert_RGB_to_rgba(c): return np.array([*(c/255),1.])
def _convert_RGBA_to_rgba(c): return c/255
def _convert_RGB_S_to_rgba(c): return _convert_RGB_to_rgba(np.array([int(v) for v in c[4:-1].split(",")]))
def _convert_RGBA_S_to_rgba(c): return _convert_RGBA_to_rgba(np.array([int(v) for v in c[5:-1].split(",")]))
def _convert_rgb_to_rgba(c): return np.array([*c,1.])
def _convert_rgba_to_rgba(c): return c
def _convert_rgb_S_to_rgba(c): return np.array([float(v) for v in c[4:-1].split(",")]+[1])
def _convert_rgba_S_to_rgba(c): return np.array([float(v) for v in c[5:-1].split(",")])
def _convert_hex_to_rgba(c):
	if c[0] == "#": c = c[1:]
	if len(c) in [6,8]:
		bytes_per_color = 2
	elif len(c) in [3,4]:
		bytes_per_color = 1
	else: raise ValueError("Cannot interpret hex color string \"{:}\"".format(c))
	if len(c)%4==0: n_nums = 4
	else: n_nums = 3
	int_rep = np.array([
		int(
			"".join(
				list(c[
					i*bytes_per_color:
					(i+1)*bytes_per_color
				])
				* (3-bytes_per_color)
			),
			base=16
		)
		for i in range(n_nums)
	])
	if len(int_rep) == 3: return _convert_RGB_to_rgba(int_rep)
	else: return _convert_RGBA_to_rgba(int_rep)
def _convert_cie_to_rgba(c): return _convert_ciea_to_rgba(np.array([*c,1.]))
def _convert_ciea_to_rgba(c):
	global _cie_to_rgb_mat
	cie_xyz = c[:3]
	c_linear = np.dot(_cie_to_rgb_mat, cie_xyz)
	rgb = np.where(
		c_linear <= 0.0031308,
		12.92 * c_linear,
		1.055 * np.power(c_linear, 1/2.4) - 0.055,
	)
	rgb = np.clip(rgb, 0, 1)
	return np.array([*rgb,c[3]])
def _convert_lms_to_rgba(c): return _convert_lmsa_to_rgba(np.array([*c,1.]))
def _convert_lmsa_to_rgba(c):
	global _lms_to_cie_mat
	lms = c[:3]
	xyz = np.dot(_lms_to_cie_mat, lms)
	return _convert_ciea_to_rgba(np.array([*xyz,c[3]]))
def _convert_oklab_to_rgba(c): return _convert_oklaba_to_rgba(np.array([*c,1.]))
def _convert_oklaba_to_rgba(c):
	global _oklab_to_lms_mat, _lms_to_cie_mat
	# OKLab to CIE xyz
	L, a, b, alpha = c
	Lab, alpha = c[:3], c[3]
	lms = np.dot(_oklab_to_lms_mat, Lab)**3
	return _convert_lms_to_rgba(np.array([*lms, alpha]))
def _convert_hsl_to_rgba(c): return _convert_hsla_to_rgba(np.array([*c,1.]))
def _convert_hsla_to_rgba(c):
	# Adapted from https://en.wikipedia.org/wiki/HSL_and_HSV#HSL_to_RGB
	H, S, L, alpha = c
	C = (1 - abs(2*L - 1)) * S
	X = C * (1 - abs((H / 60) % 2 - 1))
	m = L - C/2
	if H < 60:
		R1,G1,B1 = C,X,0
	elif H < 120:
		R1,G1,B1 = X,C,0
	elif H < 180:
		R1,G1,B1 = 0,C,X
	elif H < 240:
		R1,G1,B1 = 0,X,C
	elif H < 300:
		R1,G1,B1 = X,0,C
	else:
		R1,G1,B1 = C,0,X
	return np.array([R1+m,G1+m,B1+m,alpha])
def _convert_hsv_to_rgba(c): return _convert_hsva_to_rgba(np.array([*c,1.]))
def _convert_hsva_to_rgba(c):
	# Adapted from https://en.wikipedia.org/wiki/HSL_and_HSV#HSV_to_RGB
	H, S, V, alpha = c
	C = V * S
	X = C * (1 - abs((H / 60) % 2 - 1))
	m = V - C
	if H < 60:
		R1,G1,B1 = C,X,0
	elif H < 120:
		R1,G1,B1 = X,C,0
	elif H < 180:
		R1,G1,B1 = 0,C,X
	elif H < 240:
		R1,G1,B1 = 0,X,C
	elif H < 300:
		R1,G1,B1 = X,0,C
	else:
		R1,G1,B1 = C,0,X
	return np.array([R1+m,G1+m,B1+m,alpha])

def _convert_rgba_to_RGB(c): return np.round(c[:3]*255).astype(int)
def _convert_rgba_to_RGBA(c): return np.round(c*255).astype(int)
def _convert_rgba_to_RGB_S(c): return "RGB({},{},{})".format(*_convert_rgba_to_RGB(c))
def _convert_rgba_to_RGBA_S(c): return "RGBA({},{},{},{})".format(*_convert_rgba_to_RGBA(c))
def _convert_rgba_to_rgb(c): return c[:3]
def _convert_rgba_to_rgba(c): return c
def _convert_rgba_to_rgb_S(c): return "rgb({},{},{})".format(*_convert_rgba_to_rgb(c))
def _convert_rgba_to_rgba_S(c): return "rgba({},{},{},{})".format(*_convert_rgba_to_rgba(c))
def _convert_rgba_to_hex(c, alpha=False): return "#"+"".join(["{:02x}".format(v) for v in _convert_rgba_to_RGBA(c[:4 if alpha else 3])])
def _convert_rgba_to_cie(c): return _convert_rgba_to_ciea(c)[:3]
def _convert_rgba_to_ciea(c):
	global _rgb_to_cie_mat
	# Linearize sRGB values
	crgb = c[:3]
	c_linear = np.where(crgb <= 0.04045, crgb / 12.92, ((crgb + 0.055) / 1.055) ** 2.4)
	# Convert to XYZ using the standard matrix
	xyz = np.dot(_rgb_to_cie_mat, c_linear)
	return np.array([*xyz,c[3]])
def _convert_rgba_to_lms(c): return _convert_rgba_to_lmsa(c)[:3]
def _convert_rgba_to_lmsa(c):
	global _cie_to_lms_mat
	xyza = _convert_rgba_to_ciea(c)
	xyz, alpha = xyza[:3], xyza[3]
	# Convert XYZ to LMS
	lms = np.dot(_cie_to_lms_mat, xyz)
	return np.array([*lms,alpha])
def _convert_rgba_to_oklab(c): return _convert_rgba_to_oklaba(c)[:3]
def _convert_rgba_to_oklaba(c):
	global _cie_to_lms_mat, _lms_to_oklab_mat
	lmsa = _convert_rgba_to_lmsa(c)
	lms, alpha = lmsa[:3], lmsa[3]
	# Apply non-linearity
	lms_nonlinear = lms**(1/3)
	# Convert to Oklab
	Lab = np.dot(_lms_to_oklab_mat, lms_nonlinear)
	return np.array([*Lab,alpha])
def _convert_rgba_to_hsl(c): return _convert_rgba_to_hsla(c)[:3]
def _convert_rgba_to_hsla(c):
	# Adapted from https://en.wikipedia.org/wiki/HSL_and_HSV#RGB_to_HSL_and_HSV
	rgb = c[:3]
	maxc, minc = np.max(rgb), np.min(rgb)
	delta = maxc - minc
	L = (maxc + minc) / 2
	if delta == 0:
		H = S = 0
	else:
		S = delta / (1 - abs(2*L - 1))
		if maxc == rgb[0]:
			H = 60 * (((rgb[1] - rgb[2]) / delta) % 6)
		elif maxc == rgb[1]:
			H = 60 * (((rgb[2] - rgb[0]) / delta) + 2)
		else:
			H = 60 * (((rgb[0] - rgb[1]) / delta) + 4)
	return np.array([H,S,L,c[3]])
def _convert_rgba_to_hsv(c): return _convert_rgba_to_hsva(c)[:3]
def _convert_rgba_to_hsva(c):
	# Adapted from https://en.wikipedia.org/wiki/HSL_and_HSV#RGB_to_HSL_and_HSV
	rgb = c[:3]
	maxc, minc = np.max(rgb), np.min(rgb)
	delta = maxc - minc
	V = maxc
	if delta == 0:
		H = S = 0
	else:
		S = delta / V
		if maxc == rgb[0]:
			H = 60 * (((rgb[1] - rgb[2]) / delta) % 6)
		elif maxc == rgb[1]:
			H = 60 * (((rgb[2] - rgb[0]) / delta) + 2)
		else:
			H = 60 * (((rgb[0] - rgb[1]) / delta) + 4)
	return np.array([H,S,V,c[3]])
