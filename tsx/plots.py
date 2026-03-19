import matplotlib.pyplot as plt
from io import StringIO, BytesIO
import cartopy.crs as ccrs
from contextlib import contextmanager

@contextmanager
def figure(*args, **kwds):
	fig = plt.figure(*args, **kwds)
	try:
		yield fig
	finally:
		plt.close(fig)

light_grey = "#F4F4F4"

# These lines are necessary to stop MatplotLib from trying to initialize
# GUI backend and crashing due to not being on the main thread:
import matplotlib
matplotlib.use('agg')

def rendered_plot_data(fig, format):
	if format == 'svg':
		svg_data = StringIO()
		fig.savefig(svg_data, format='svg')
		return bytes(svg_data.getvalue(), encoding="utf8")
	elif format == 'png':
		png_data = BytesIO()
		fig.savefig(png_data, format='png', dpi=180)
		return png_data.getvalue()
	else:
		raise ValueError("Format unsupported: %s" % format)

def consistency_plot(data, format=None):
	xys = [(year, i + 1) for i, series in enumerate(data) for year, count in series]
	x, y = zip(*xys)

	with figure(figsize=(6, 4.5)) as fig:
		ax = fig.gca()
		ax.yaxis.get_major_locator().set_params(integer=True)
		ax.xaxis.get_major_locator().set_params(integer=True)
		plt.xlabel('Year')
		plt.ylabel('Sites (time series)')
		plt.grid(True, color='#ddd')
		plt.plot(x, y, 'ko', ms=5)
		return rendered_plot_data(fig, format)


def trend_plot(data, assume_single_species=True, format=None):
	rows = data.split("\n")

	rows = [row for row in rows if len(row) > 0 and "NA" not in row and "LPI" not in row]
	series = list(zip(*[[float(x.strip('"')) for x in row.split(" ")] for row in rows]))

	(years, trend, lower, upper, num_species) = series[0:5]

	years = [int(year) for year in years]

	with figure(figsize=(12, 4.5)) as fig:
		plt.xlabel('Year')
		plt.ylabel('Index (%s = 1)' % years[0])
		plt.grid(True, color='#ddd')


		if assume_single_species:
			plt.plot(years, trend, linestyle='dashed')
		else:
			num_species = [int(x) for x in num_species]
			single_species = [x == 1 for x in num_species]
			single_species_dilated = [a or b or c for a, b, c in zip(
				single_species[1:] + [False],
				single_species,
				[False] + single_species[:-1])
			]
			trend_solid = [None if single_species[i] else trend[i] for i in range(len(trend))]
			trend_dashed = [trend[i] if single_species_dilated[i] else None for i in range(len(trend))]

			plt.plot(years, trend_solid, color='tab:blue')
			plt.plot(years, trend_dashed, color='tab:blue', linestyle='dashed')

		plt.gca().set_xlim(years[0], years[-1])
		ax = fig.gca()
		ax.xaxis.get_major_locator().set_params(integer=True)
		# Note: hatch fill doesn't work because it produces an SVG that PyPDF can't render
		plt.fill_between(years, lower, upper, color=light_grey)

		return rendered_plot_data(fig, format)

def intensity_map(data, format=None):
	xs = [p["lon"] for p in data]
	ys = [p["lat"] for p in data]

	map_projection = ccrs.AlbersEqualArea(
		central_longitude=135,
		central_latitude=-25,
		standard_parallels=(-35,-10))

	with figure(figsize=(6, 4.5)) as fig:
		ax = fig.add_subplot(projection=map_projection)
		buffer = 7
		minx = min(min(xs) - buffer, 110)
		maxx = max(max(xs) + buffer, 160)
		miny = min(min(ys) - buffer, -45)
		maxy = max(max(ys) + buffer, -5)

		ax.set_extent([minx, maxx, miny, maxy])
		# ax.add_feature(cfeature.LAND)
		# ax.add_feature(cfeature.OCEAN)
		ax.coastlines()
		gl = ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False, color='#00000020')
		gl.top_labels = False
		gl.right_labels = False

		scale = 1.5
		ax.plot(xs, ys, marker='o', linewidth=0, transform=ccrs.Geodetic(), mfc='#6C85CC40', mew=0,  markersize=10 * scale)
		ax.plot(xs, ys, marker='o', linewidth=0, transform=ccrs.Geodetic(), mfc='#6C85CC80', mew=0,  markersize=9 * scale)
		ax.plot(xs, ys, marker='o', linewidth=0, transform=ccrs.Geodetic(), mfc='#FD49FB80', mew=0, markersize=7 * scale)

		return rendered_plot_data(fig, format)

def summary_plot(data, format=None):
    xys = [(int(year), n) for (year, n) in data['timeseries'].items()]

    x, y = zip(*xys)

    with figure(figsize=(6, 4.5)) as fig:
	    ax = fig.gca()
	    ax.yaxis.get_major_locator().set_params(integer=True)
	    ax.xaxis.get_major_locator().set_params(integer=True)
	    plt.xlabel('Year')
	    plt.ylabel('Number of time series', color='g')
	    plt.grid(True, color='#ddd')
	    plt.plot(x, y, 'go', ms=5)

	    if 'taxa' in data:
	        xys = [(int(year), n) for (year, n) in data['taxa'].items()]
	        x, y = zip(*xys)
	        ax2 = ax.twinx()
	        ax2.yaxis.get_major_locator().set_params(integer=True)
	        ax2.set_ylabel('Number of taxa', color='b')
	        ax2.plot(x, y, 'bo', ms=5)

	    return rendered_plot_data(fig, format)
