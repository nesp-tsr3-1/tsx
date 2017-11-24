#!/usr/bin/env python
import fiona
import shapely.geometry as geometry
from shapely.ops import cascaded_union, polygonize, transform
from scipy.spatial import Delaunay
from scipy.spatial import KDTree
import numpy as np
from functools import partial
import pyproj
import math
from math import sin, cos, sqrt, atan2, radians
import sys, os, getopt
from shapely.geometry import shape, Point, MultiPolygon
from nesp.geo import to_multipolygon, subdivide_geometry, fast_difference
from nesp.util import run_parallel
from nesp.db import get_session
import nesp.config
from tqdm import tqdm
import logging
import shapely.wkb

log = logging.getLogger(__name__)

def plot_polygon(polygon):
    # These imports are only needed for plotting
    import pylab as pl
    from descartes import PolygonPatch

    fig = pl.figure(figsize=(10,10))
    ax = fig.add_subplot(111)
    margin = .3
    x_min, y_min, x_max, y_max = polygon.bounds
    ax.set_xlim([x_min-margin, x_max+margin])
    ax.set_ylim([y_min-margin, y_max+margin])
    patch = PolygonPatch(polygon, fc='#999999',
                         ec='#000000', fill=True,
                         zorder=-1)
    ax.add_patch(patch)
    return fig

def add_edge_points(edges, edge_points, coords, i, j):
    """
    Add a line between the i-th and j-th points,
    if not in the list already
    """
    if (i, j) in edges or (j, i) in edges:
        # already added
        return
    edges.add( (i, j) )
    edge_points.append(coords[ [i, j] ])

def add_edge(edges, coords, i, j):
    """
    Add a line between the i-th and j-th points,
    if not in the list already
    """
    i, j = sorted((i, j))
    if (i, j) in edges or (j, i) in edges:
        # already added
        return
    edges.add( (i, j) )

def alpha_shape(coords, alpha):
    """
    Create alpha shape in following Burgman and Fox paper.
    """
    # Return empty geometry if not enough points
    if len(coords) < 3:
        return MultiPolygon(), None

    try:
        tri = Delaunay(coords)
    except:
        print coords
        raise
    alledges=set() #Use a set so lines are not duplicated
    for ia, ib, ic in tri.vertices:
        add_edge(alledges, coords, ia, ib)
        add_edge(alledges, coords, ib, ic)
        add_edge(alledges, coords, ic, ia)

    lengths=[]
    for i,j in alledges:
        startx,starty=coords[ [i, j] ][0]
        stopx,stopy=coords[ [i, j] ][1]
        #Use coordinates to get mean length
        lengths+=[np.sqrt(abs(startx-stopx)**2 + abs(starty-stopy)**2)]

    meanLengths=sum(lengths)/len(lengths)
    alphadistance = meanLengths*alpha # in meters'
    #print "meanlength=%f, alphadistance=%f" %(meanLengths, alphadistance)
    # all edges less than alpha distance
    edges=set()
    edge_points = []
    for ia, ib, ic in tri.vertices:
        pa = coords[ia]
        pb = coords[ib]
        pc = coords[ic]
        a = math.sqrt((pa[0]-pb[0])**2 + (pa[1]-pb[1])**2)
        b = math.sqrt((pb[0]-pc[0])**2 + (pb[1]-pc[1])**2)
        c = math.sqrt((pc[0]-pa[0])**2 + (pc[1]-pa[1])**2)
        if (a+b+c)/3 < alphadistance:
            add_edge_points(edges, edge_points, coords, ia, ib)
            add_edge_points(edges, edge_points, coords, ib, ic)
            add_edge_points(edges, edge_points, coords, ic, ia)

    m = geometry.MultiLineString(edge_points)
    triangles = list(polygonize(m))
    return cascaded_union(triangles), edge_points

# def thinning(coords, thinning_distance):
#     """
#     """
#     kdtree = KDTree(coords)
#     _used = set()    # ids of points being used
#     _removed = set() # ids of points being removed
#     _list  = sorted(kdtree.query_pairs(thinning_distance)) # replace by thinning distance
#     for _element in _list:
#         if _used.issuperset(set([_element[0]])):
#             _removed.add(_element[1])
#         elif _used.issuperset(set([_element[1]])):
#             _removed.add(_element[0])
#         elif _removed.issuperset(set([_element[1]])):
#             _used.add(_element[0])
#             _removed.add(_element[1])
#         else:
#             _used.add(_element[1])
#             _removed.add(_element[0])

#     #print "coords length=%d"%(len(coords))
#     #print "list length=%d"%(len(_list))
#     #print "used length=%d"%(len(_used))
#     #print "removed length=%d"%(len(_removed))
#     for i in range(0, len(coords)):
#         if not _used.issuperset(set([i])) and not _removed.issuperset(set([i])):
#             _used.add(i)
#     return np.array([coords[i]  for i in _used])

# JW - Simpler version of thinning function
def thinning(coords, thinning_distance):
    """
    Removes points from coords such that no two points remain within thinning_distance of each other
    """
    kdtree = KDTree(coords)
    removed = set()

    for a, b in sorted(kdtree.query_pairs(thinning_distance)):
        # At least one of a or b should be removed:
        if a not in removed and b not in removed:
            removed.add(b)

    return np.array([coord for i, coord in enumerate(coords) if i not in removed])

def make_alpha_hull(points, coastal_shape,
                    thinning_distance=250, alpha=1.6,
                    hullbuffer_distance=1000, isolatedbuffer_distance=1000):
    """
    """
    coords = np.array([point.coords[0] for point in points])
    thinned_list = thinning(coords, thinning_distance)
    # print thinned_list
    concave_hull, edge_points = alpha_shape(thinned_list,alpha=alpha)
    # buffer
    alpha_hull_buff = concave_hull.buffer(hullbuffer_distance)
    # now get the isolated points
    multipoint = geometry.MultiPoint(points)
    # single_points = multipoint.difference(alpha_hull_buff).buffer(isolatedbuffer_distance) # slow
    single_points = fast_difference(multipoint, alpha_hull_buff).buffer(isolatedbuffer_distance)
    final = alpha_hull_buff.union(single_points)

    #clipping
    return final.intersection(coastal_shape)
    #_ = plot_polygon(final)
    #pl.show()

def process_database(species = None, commit = False):
    """
    Generates alpha hulls from raw sighting data in the database

    Intersects alpha hulls with range layers, and inserts the result back into the database
    """
    session = get_session()

    if species is None:
        species = get_all_spno(session)

    if commit:
        for spno in species:
            session.execute("""
                DELETE FROM taxon_presence_alpha_hull
                WHERE taxon_id IN (SELECT id FROM taxon WHERE spno = :spno)
                """, { 'spno': spno })
            session.execute("""
                DELETE FROM taxon_presence_alpha_hull_subdiv
                WHERE taxon_id IN (SELECT id FROM taxon WHERE spno = :spno)
                """, { 'spno': spno })
        session.commit()

    db_proj = pyproj.Proj('+init=EPSG:4326') # Database always uses WGS84
    working_proj = pyproj.Proj('+init=EPSG:3112') # GDA94 / Geoscience Australia Lambert - so that we can buffer in metres

    # Load coastal shapefile
    coastal_shape_filename = nesp.config.config.get("processing.alpha_hull", "coastal_shp")
    with fiona.open(coastal_shape_filename, 'r') as coastal_shape:
        # Convert from fiona dictionary to shapely geometry and reproject
        coastal_shape = reproject(shape(coastal_shape[0]['geometry']), pyproj.Proj(coastal_shape.crs), working_proj)
        # Simplify coastal boundary - makes things run ~20X faster
        log.info("Simplifying coastal boundary")
        coastal_shape = coastal_shape.buffer(10000).simplify(10000)

    log.info("Generating alpha shapes")

    # Process a single species.
    # This gets run off the main thread.
    def process_spno(spno):
        session = get_session()
        try:
            # Get raw points from DB
            raw_points = get_species_points(session, spno)

            if len(raw_points) < 4:
                # Not enough points to create an alpha hull
                return

            # Read points from database
            points = [reproject(p, db_proj, working_proj) for p in raw_points]

            # Generate alpha shape
            alpha_shp = make_alpha_hull(
                points = points,
                coastal_shape = coastal_shape,
                thinning_distance = nesp.config.config.getfloat('processing.alpha_hull', 'thinning_distance'),
                alpha = nesp.config.config.getfloat('processing.alpha_hull', 'alpha'),
                hullbuffer_distance = nesp.config.config.getfloat('processing.alpha_hull', 'hullbuffer_distance'),
                isolatedbuffer_distance = nesp.config.config.getfloat('processing.alpha_hull', 'isolatedbuffer_distance'))

            # Convert back to DB projection
            alpha_shp = reproject(alpha_shp, working_proj, db_proj)

            # Clean up geometry
            alpha_shp = alpha_shp.buffer(0)

            # Get range polygons to intersect with alpha shape
            for taxon_id, range_id, breeding_range_id, geom_wkb in get_species_range_polygons(session, spno):
                # Intersect and insert into DB
                geom = shapely.wkb.loads(geom_wkb).buffer(0)
                geom = to_multipolygon(geom.intersection(alpha_shp)) # slow
                if len(geom) > 0:
                    session.execute("""INSERT INTO taxon_presence_alpha_hull (taxon_id, range_id, breeding_range_id, geometry)
                        VALUES (:taxon_id, :range_id, :breeding_range_id, ST_GeomFromWKB(_BINARY :geom_wkb))""", {
                            'taxon_id': taxon_id,
                            'range_id': range_id,
                            'breeding_range_id': breeding_range_id,
                            'geom_wkb': shapely.wkb.dumps(geom)
                        }
                    )
                # We also subdivide the geometries into small pieces and insert this into the database. This allows for much faster
                # spatial queries in the database.
                for subgeom in subdivide_geometry(geom, max_points = 100):
                    session.execute("""INSERT INTO taxon_presence_alpha_hull_subdiv (taxon_id, range_id, breeding_range_id, geometry)
                        VALUES (:taxon_id, :range_id, :breeding_range_id, ST_GeomFromWKB(_BINARY :geom_wkb))""", {
                            'taxon_id': taxon_id,
                            'range_id': range_id,
                            'breeding_range_id': breeding_range_id,
                            'geom_wkb': shapely.wkb.dumps(subgeom)
                        }
                    )
            if commit:
                session.commit()

        except:
            log.exception("Exception processing alpha hull")
            raise
        finally:
            session.close()

    # Process all the species in parallel
    for result, error in tqdm(run_parallel(process_spno, species), total = len(species)):
        if error:
            print error

def reproject(geom, src_proj, dest_proj):
    fn = partial(pyproj.transform, src_proj, dest_proj)
    return transform(fn, geom)

def get_all_spno(session):
    return [spno for (spno,) in session.execute("SELECT DISTINCT spno FROM taxon").fetchall()]

def get_species_points(session, spno):
    # TODO - get points from type 1 data too
    sql = """SELECT DISTINCT ST_X(coords), ST_Y(coords)
        FROM t2_survey, t2_sighting, taxon
        WHERE survey_id = t2_survey.id
        AND taxon_id = taxon.id
        AND spno = :spno"""

    return [Point(x,y) for x, y in session.execute(sql, { 'spno': spno }).fetchall()]

def get_species_range_polygons(session, spno):
    return session.execute("""SELECT taxon_id, range_id, breeding_range_id, ST_AsWKB(geometry)
                        FROM taxon_range, taxon
                        WHERE taxon_id = taxon.id
                        AND spno = :spno
                        """, { 'spno': spno }).fetchall()

# The rest of the functions below are only used when this file is called as a stand-alone script
# (Leaving this here from Hoang's original script)

def generate_alphashape(infile, outfile, inproj, outproj, coastal_shape,
                        thinning_distance, alpha,
                        hullbuffer_distance, isolatedbuffer_distance):
    """
    """
    with fiona.open(infile) as i_shape:
        if inproj == None or inproj.strip() == '':
            # get spno
            inproj= "+proj=" + i_shape.meta['crs']['proj']
            inproj += " +ellps=" + i_shape.meta['crs']['ellps']
            inproj += " +towgs84=0,0,0,0,0,0,0"
            if i_shape.meta['crs']['no_defs'] == 'True':
                inproj += " +no_defs"
        project = partial(pyproj.transform,
                          pyproj.Proj(inproj),  #
                          pyproj.Proj(init=outproj))

        occurence_points_proj = [transform(project, geometry.shape(point['geometry'])) for point in i_shape]

        spno=i_shape[0]['properties']['SpNo']

        c_shape = fiona.open(coastal_shape)
        c_shape_proj = transform(project, geometry.shape(c_shape[0]['geometry']))
        alpha_shp = make_alpha_hull(occurence_points_proj, c_shape_proj, \
                                    thinning_distance, alpha, \
                                    hullbuffer_distance,isolatedbuffer_distance)

        # write this
        schema = {'geometry': 'Polygon',
                'properties': fiona.OrderedDict([(u'Shape_Leng', 'float:19.11'), \
                           (u'Shape_Area', 'float:19.11'), (u'SPNO', 'int:9')])}
        with fiona.open(outfile, 'w', 'ESRI Shapefile', schema) as c:
            ## If there are multiple geometries, put the "for" loop here
            for shape in alpha_shp:
                c.write({
                    'geometry': geometry.mapping(shape),
                    'properties': fiona.OrderedDict([('Shape_Leng', shape.length), \
                           ('Shape_Area', shape.area), ('SPNO', spno)])
                        })

def usage():
    """
    Print the usaga
    """
    print "alpha hull script"
    print "To print help:"
    print "                 alphahull.py -h"
    print "To create alpha hulls:"
    print "                 alphahull.py -i infile -o outfile -t thinning_distance"
    print "                              -a alpha -b alpha_hull_buffer -s isolated_distance"
    print "                              -p outproj -q inproj"

def main(argv):
    """
    main function: parse the parameters
    """
    try:
        opts, args = getopt.getopt(argv, 'h:i:o:t:a:b:s:p:q:')
    except getopt.GetoptError as err:
        usage()
        sys.exit(1)
    inproj = None
    outproj = 'epsg:3112'
    infile = ''
    outfile = ''
    coastshp = 'AusCoast_Islands_1kmBuffer.shp'
    thinning_distance=250
    alpha=1.6
    hullbuffer_distance=1000
    isolatedbuffer_distance=1000
    for _opt_pair in opts:
        if len(_opt_pair) == 0:
            continue
        if _opt_pair[0] == '-h':
            usage()
            sys.exit()
        elif _opt_pair[0] == '-i': # input file
            infile = _opt_pair[1]
        elif _opt_pair[0] == '-o': # output file
            outfile = _opt_pair[1]
        elif _opt_pair[0] == '-t': # thinning
            thinning_distance = float(_opt_pair[1])
        elif _opt_pair[0] == '-a': # alpha
            alpha = float(_opt_pair[1])
        elif _opt_pair[0] == '-b': # alpha hull buffer
            hullbuffer_distance =  float(_opt_pair[1])
        elif _opt_pair[0] == '-s': # isolated buffer
            isolatedbuffer_distance = float(_opt_pair[1])
        elif _opt_pair[0] == '-p': # out proj
            outproj = _opt_pair[1]
        elif _opt_pair[0] == '-q': # in proj
            inproj = _opt_pair[1]

    # print "infile=%s, outfile=%s" %(infile, outfile)
    generate_alphashape(infile, outfile, inproj, outproj,
                        coastshp, thinning_distance, alpha,
                        hullbuffer_distance, isolatedbuffer_distance)

if __name__ == '__main__':
    main(sys.argv[1:])
