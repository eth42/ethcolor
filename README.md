# ethcolor
A basic python package to generate, organize, expand, and optimize accessible color palettes.
This packages is aimed at scientific plots, where the differentiability of colors is way more important than the "beauty" of a palette.
The main goal is thus, to have very distinguishable colors for colorblind and non-colorblind people, rather than a pretty combination of (often similar in tone) colors.

## Color Spaces
This package provides the wrapper class `Color` for color specifications, which contains the (numeric/string) representation as well as a declaration of the color space.
The available color spaces are listed in the enum class `COLOR_FORMATS` and include Hex, RGB, HSL, HSV, CIE XYZ, OKLAB, and LMS, each with and without alpha channel.
Using either the `Color.get_value(space)` method or the `convert_color` function, one can easily translate from one color space to the other.
Most functions also accept "raw" inputs such as `RGB(100,50,10)`, which are automatically parsed as follows:

- Format `HEX`: Strings starting with `#` are interpret as hex colors. Strings of length 3 or 6 are considered RGB values and strings of length 4 and 8 are considered RGBA values.
- Formats `RGB_S` and `RGBA_S`: Strings of the type `RGB(..., ..., ...)` and `RGBA(..., ..., ...)` are considered RGB and RGBA values with values ranging from 0 to 255.
- Formats `rgb_S` and `rgba_S`: Strings of the type `rgb(..., ..., ...)` and `rgba(..., ..., ...)` are considered RGB and RGBA values with float values ranging from 0 to 1.
- Formats `RGB` and `RGBA`: Integer numpy arrays of length 3 or 4 are considered RGB and RGBA values with values ranging from 0 to 255.
- Formats `rgb` and `rgba`: Float numpy arrays of length 3 or 4 are considered RGB and RGBA values with float values ranging from 0 to 1.

All other color formats should be instantiated using the `Color` class or calls like `convert_color(np.array([.5,.3,.4]), COLOR_FORMATS.OKLAB, COLOR_FORMATS.rgba)`.

## Palette Management
This package contains the classes `PaletteManager` and `Palette`.
A `Palette` has a name and should contain multiple named colors, provided as a list of lists `[name, color]` (as the `color` will be replaced, this must be a list, not a tuple).
Internally, all colors are first translated to the floating-point `rgba` space, but the getters allow for arbitrary color spaces.
The `PaletteManager` can contain multiple `Palette`s. The first added `Palette` will be considered the default palette until otherwise specified.
A default `PaletteManager` with a few predefined color palettes can be accessed under the name `default_palettes`.

## Palette Modifications
One of the main goals of this package is to provide an easy way to adapt your color palettes to different types of color blindness.
For that purpose, the function `optimize_palette` can be called, which takes an iterable of colors or a `Palette` object and some optimization parameters and produces a modified palette, which is better differentiable by colorblind (and non-colorblind) people.

To create a new random palette, you can use `random_colors` (which automatically calls `optimize_palette`) and to extend an existing palette, you can use `extend_colors` (which isn't all that good to be honest).

## Interpolating/Viewing/Printing colors
To interpolate between colors, you can either mix two colors with `color_mix` or create a series of interpolated colors with `interpolate_colors`.
Mixing/interpolation by default uses the OKLAB color space, which allows for "perceived" linear blending of colors (see color theory, it's complicated).
Other color spaces for interpolation can be set as an argument.
To create a continuous color gradient over multiple colors, you can use the `interpolate_color_series` function.

To view colors, you can use the `display_palette` function which either takes a list of colors or a `Palette` and displays all the colors in a horizontal bar where each color occupies the same horizontal space.
You can also use the `create_plotly_scale` function to translate your colors/`Palette` into the format of a plotly color scale.

To print colors, you can convert them to the string formats `RGB_S`, `RGBA_S`, `rgb_S`, `rgba_S`, and `HEX` and access their strings by calling `Color.get_value()`.

## Examples

Loading the plotly default palette, modifying it for better visibility and displaying the original and the optimized version in the IPython shell:

```python
import ethcolor
palette = ethcolor.default_palettes.get_palette("plotly")
# Set change_weight to a high value to not move to far away from the original palette
opt_palette = ethcolor.optimize_palette(palette, change_weight=.8)
ethcolor.display_palette(palette)
ethcolor.display_palette(opt_palette)
```

Creating a random color palette and adding it to the default palette manager:

```python
import ethcolor
import numpy as np
# Seeding of the numpy random generator for reproducible palette generation
np.random.seed(42)
colors = ethcolor.random_colors(8)
palette = ethcolor.Palette("random", [
	[f"random{i}", c]
	for i,c in enumerate(colors)
])
ethcolor.default_palettes.add_palette(palette)
# Displaying the new palette
ethcolor.display_palette(ethcolor.default_palettes.get_palette("random"))
```

Creating a color gradient and using it as a color scale in a plotly figure:

```python
import ethcolor
import numpy as np
import plotly.graph_objects as go
# Define start, mid, and end color of the color scale
start_color = "RGB(245,120,  4)"
mid_color   = "RGB(255,255,255)"
end_color   = "RGB( 22, 56,209)"
# Get a high resolution interpolation in OKLAB space, rather than plotlys RGB interpolation
interpolated_colors = ethcolor.interpolate_color_series([start_color, mid_color, end_color], 200)
# Create the plotly colorscale
colorscale = ethcolor.create_plotly_scale(interpolated_colors)
# Create a basic scatter dataset
x,y = np.random.sample((2,2000))
z = np.sin(4*np.pi*x) * np.cos(5*np.pi*y)
# Make the plot
go.Figure(
	go.Scatter(
		x=x,
		y=y,
		mode="markers",
		marker_cmin=-1,
		marker_cmax=+1,
		marker_color=z,
		marker_colorscale=colorscale,
		marker_showscale=True,
	),
	layout_yaxis_scaleanchor="x",
).show()
```


