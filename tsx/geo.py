# Geospatial utils
from collections import deque
import time
from shapely.geometry import Point, MultiPoint, Polygon, MultiPolygon, GeometryCollection, LineString, LinearRing, shape
from shapely.ops import transform
from functools import partial
import pyproj
from contextlib import contextmanager
import fiona

def reproject_fn(src_proj, dest_proj):
	transformer = pyproj.Transformer.from_proj(src_proj, dest_proj, always_xy=True)
	return lambda geom: transform(transformer.transform, geom)


# Opening a shapefile and reprojecting it is really verbose
@contextmanager
def open_shapefile(filename, dest_crs):
	with fiona.Env(OSR_WKT_FORMAT="WKT2_2018"), fiona.open(filename, encoding = 'Windows-1252') as shp:
		src_crs = pyproj.CRS.from_wkt(shp.crs_wkt)
		transformer = pyproj.Transformer.from_proj(src_crs, dest_crs, always_xy=True)
		reproject = lambda geom: transform(transformer.transform, geom)
		yield shp, reproject

def subdivide_geometry(geometry, max_points = 100, max_extent = None):
	"""
	Subdivides a geometry into pieces having no more than max_points points each
	"""
	q = deque([geometry])

	while len(q) > 0:
		# Get next geometry to process from queue
		geom = q.pop()
		points_ok = max_points is None or count_points(geom) <= max_points
		extent_ok = max_extent is None or extent(geom) <= max_extent
		if points_ok and extent_ok:
			yield geom
		else:
			# Intersect geometry with each half of its bounding box, and add to work queue
			for b in split_bounds(*geom.bounds):
				q.append(geom.intersection(Polygon.from_bounds(*b)))

def extent(geom):
	minx, miny, maxx, maxy = geom.bounds
	return max(maxx - minx, maxy - miny)

def split_bounds(minx, miny, maxx, maxy):
	"""
	Splits the bounding box in half across it's shortest dimension
	"""
	if maxy - miny > maxx - minx:
		midy = (miny + maxy) / 2
		return [(minx, miny, maxx, midy), (minx, midy, maxx, maxy)]
	else:
		midx = (minx + maxx) / 2
		return [(minx, miny, midx, maxy), (midx, miny, maxx, maxy)]

def to_multipolygon(geom):
	"""
	Converts a geometry to a MultiPolygon

	Non-polygonal geometries are dropped
	"""
	if type(geom) == MultiPolygon:
		return geom
	elif type(geom) == Polygon:
		return MultiPolygon([geom])
	elif type(geom) == GeometryCollection:
		return MultiPolygon([poly for g in geom.geoms for poly in to_multipolygon(g).geoms])
	else:
		return MultiPolygon([])

def tile_key_fn(bounds):
	minx, miny, maxx, maxy = bounds
	w = maxx - minx
	h = maxy - miny
	def tile_key(x, y, z):
		x = int((1 << z) * (x - minx) / w)
		y = int((1 << z) * (y - miny) / h)
		return (x, y, z)
	return tile_key

def tile_bounds_fn(bounds):
	bminx, bminy, bmaxx, bmaxy = bounds
	bw = bmaxx - bminx
	bh = bmaxy - bminy
	def tile_bounds(key):
		x, y, z = key
		minx = float(x * bw) / (1 << z) + bminx
		miny = float(y * bh) / (1 << z) + bminy
		maxx = float((x + 1) * bw) / (1 << z) + bminx
		maxy = float((y + 1) * bh) / (1 << z) + bminy
		return Polygon.from_bounds(minx, miny, maxx, maxy)
	return tile_bounds

def tile_key(x, y, z):
	x = int((1 << z) * (x + 180) / 360)
	y = int((1 << z) * (y + 90) / 180)
	return (x, y, z)

def tile_bounds(key):
	x, y, z = key
	# Back to lat, lon range
	minx = float(x * 360) / (1 << z) - 180
	miny = float(y * 180) / (1 << z) - 90
	maxx = float((x + 1) * 360) / (1 << z) - 180
	maxy = float((y + 1) * 180) / (1 << z) - 90

	return Polygon.from_bounds(minx, miny, maxx, maxy)

def count_points(geom):
	"""Counts the number of points in a geometry"""
	if geom.is_empty:
		return 0
	if type(geom) == Point:
		return 1
	if type(geom) == Polygon:
		return len(geom.exterior.coords) + sum([len(i.coords) for i in geom.interiors])
	if type(geom) in (LineString, MultiPoint):
		return len(geom)
	else:
		return sum([count_points(g) for g in geom.geoms])

def point_intersects_geom(poly, x, y, cache, z = 2, tile_key = None, tile_bounds = None): # z = 2 chosen based on testing
	"""
	Fast point in polygon test that uses a cache to speed up results

	The cache parameter should be an empty dictionary on the first call, and then reused on
	subsequent calls with the same polygon
	"""
	if z > 18:
		return poly.intersects(Point(x, y))

	if tile_key == None:
		if 'tile_key' not in cache:
			cache['tile_key'] = tile_key_fn(poly.bounds)
			cache['tile_bounds'] = tile_bounds_fn(poly.bounds)

		tile_key = cache['tile_key']
		tile_bounds = cache['tile_bounds']

	key = tile_key(x, y, z)

	if key not in cache:
		bounds = tile_bounds(key)
		intersection = poly.intersection(bounds)

		if intersection.is_empty:
			cache[key] = False
		elif intersection == bounds:
			cache[key] = True
		else:
			cache[key] = intersection

	val = cache[key]

	if val == True:
		return True
	elif val == False:
		return False
	else:
		return point_intersects_geom(val, x, y, cache, z = z + 2, tile_key = tile_key, tile_bounds = tile_bounds) # z + 2 chosen based on testing

def fast_difference(a, b):
	# We can extend this to other geometry types if we want
	if type(b) not in (Polygon, MultiPolygon) and type(a) != MultiPoint:
		raise ValueError("Unsupported geometry types")

	if b.is_empty:
		return a

	cache = {}
	result = []
	for point in a.geoms:
		if not point_intersects_geom(b, point.x, point.y, cache):
			result.append(point)

	return MultiPoint(result)
