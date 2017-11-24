# Geospatial utils
from collections import deque
import time
from shapely.geometry import Point, MultiPoint, Polygon, MultiPolygon, GeometryCollection, LineString, LinearRing, shape
from shapely.ops import transform
from functools import partial
import pyproj

# def subdivide_geometry(geometry, max_points = 1000):
# 	"""
# 	Subdivides a geometry into pieces having no more than max_points points each
# 	"""
# 	tiles = deque()
# 	tiles.append((0,0,0,geometry))

# 	while len(tiles) > 0:
# 		x, y, z, geom = tiles.pop()
# 		if count_points(geom) <= max_points:
# 			yield geom
# 		else:
# 			z2 = z + 1
# 			for x2 in [x * 2, x * 2 + 1]:
# 				for y2 in [y * 2, y * 2 + 1]:
# 					geom2 = to_multipolygon(geom.intersection(tile_bounds((x2, y2, z2))))
# 					if not geom2.is_empty:
# 						tiles.append((x2, y2, z2, geom2))

def reproject(geom, src_proj, dest_proj):
    return reproject_fn(src_proj, dest_proj)(geom)

def reproject_fn(src_proj, dest_proj):
	fn = partial(pyproj.transform, src_proj, dest_proj)
	return lambda geom: transform(fn, geom)

def subdivide_geometry(geometry, max_points = 100):
	"""
	Subdivides a geometry into pieces having no more than max_points points each
	"""
	q = deque([geometry])

	while len(q) > 0:
		# Get next geometry to process from queue
		geom = q.pop()
		if count_points(geom) <= max_points:
			yield geom
		else:
			# Intersect geometry with each half of its bounding box, and add to work queue
			for b in split_bounds(*geom.bounds):
				q.append(geom.intersection(Polygon.from_bounds(*b)))

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
		return MultiPolygon([poly for g in geom for poly in to_multipolygon(g)])
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
		return sum([count_points(g) for g in geom])

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
