# Improved alpha hull code - much more efficient than previous version
# Not currently used

import numpy as np
from scipy.spatial import Delaunay
import matplotlib.pyplot as plt
from types import SimpleNamespace
import shapely
import shapely.validation

def simplex_inclusion(delaunay_triangulation, alpha, strategy):
    points = delaunay_triangulation.points
    simplices = delaunay_triangulation.simplices

    if strategy == 'circumcircle':
        # Determine whether the circumcircle diameter of each triangle is greater than the alpha parameter.
        # The circumcircle diameter of a triangle is equal to abc/2A where a, b and c are the lengths of the
        # sides, and A is the triangle area.
        # For better performance and numerical stability, we do not calculate the diameter directly, but rather
        # the square of the numerator and denominator of the above formula, i.e. (abc)^2 and 4A^2.
        # We can then check against the alpha value via alpha^2 * B > A
        v = points[simplices]
        (x, y) = np.moveaxis(v, [0, 1, 2], [1, 2, 0])

        xr = np.roll(x, 1, axis=1)
        yr = np.roll(y, 1, axis=1)

        xd = x - xr
        ys = y + yr
        yd = y - yr

        A = np.prod(xd**2 + yd**2, axis=1) #(abc)^2
        B = np.sum(xd * ys, axis=1)**2     #4A^2

        inc = (alpha ** 2) * B > A
        return inc

    elif strategy == 'mean_edge_length':
        # From Burgman & Fox paper (2003)
        v = points[simplices]
        (x, y) = np.moveaxis(v, [0, 1, 2], [1, 2, 0])

        xr = np.roll(x, 1, axis=1)
        yr = np.roll(y, 1, axis=1)

        xd = x - xr
        yd = y - yr

        A = np.mean(np.sqrt(xd**2 + yd**2), axis=1)
        B = np.mean(np.sqrt(xd**2 + yd**2))

        inc = alpha * B > A
        return inc

    else:
        raise ValueError('Unknown strategy: %s' % strategy)


def trace_rings(delaunay_triangulation, simplex_inclusion):
    inc = simplex_inclusion
    d = delaunay_triangulation
    points = d.points

    # TODO: use label_polygons to associate polygons with holes instead of needing to polygonize

    # Form polygon boundaries and holes by following boundary edges

    # Boundary edges are edges belonging to an included triangle, that is not a neighbour of of
    # another included triangle
    is_boundary = np.expand_dims(inc, axis=1) * np.logical_or(d.neighbors == -1, ~inc[d.neighbors])

    # Calculate opposite vertex in neighbouring simplex (only valid where a neighbour exists)
    vsum = np.sum(d.simplices, axis=1)
    opp = vsum[d.neighbors] - np.expand_dims(vsum, axis=1) + d.simplices
    opp_match = d.simplices[d.neighbors] == np.expand_dims(opp, axis=2)
    opp_index = np.sum(opp_match * np.tile([0,1,2], (len(d.simplices), 3, 1)), axis=2)

    # Determine which edge should be visited next for the purposes of building polygon boundaries/holes.
    # This is a bit tricky. If an edge is a boundary edge, then the next edge to be examined is the next
    # edge of the current simplex. Otherwise, it should flip over to complementary edge of the neighbouring
    # simplex and then follow the next edge in that simplex.
    next_simplex = np.where(is_boundary, np.expand_dims(np.arange(len(d.simplices)), axis=1), d.neighbors)
    next_vertex = np.where(is_boundary, [1,2,0], (opp_index + 1) % 3)

    # This is the step where we actually build the polygon boundaries/holes. Due to the non-linear
    # nature of visiting edges, we have to use a Python loop rather than vectorised numpy code.
    # But, it's just a single O(n) pass, so performance is not too bad.
    processed = np.full(d.simplices.shape, False)


    last_visit = np.full(len(points), -1)
    t = 0

    rings = []
    for i in range(len(d.simplices)):
        for j in range(0,3):
            if is_boundary[i][j] and not processed[i][j]:
                cs, cv = i, j # current simplex, current vertex
                t0 = t
                ring = []
                while not processed[cs][cv]:
                    if is_boundary[cs][cv]:
                        processed[cs][cv] = True
                        p = d.simplices[cs][(cv + 1) % 3]
                        ring.append(p)

                        if last_visit[p] >= t0:
                            t = last_visit[p]
                            ring, subring = ring[:(t - t0)], ring[(t - t0):]
                            rings.append(shapely.LinearRing(points[subring]))
                        else:
                            t += 1
                            last_visit[p] = t

                    cs, cv = next_simplex[cs][cv], next_vertex[cs][cv]
                rings.append(shapely.LinearRing(points[ring]))

    return rings



def multipolygon_from_rings(rings):
    polygons = [(shapely.Polygon(r), []) for r in rings if r.is_ccw]
    for r in rings:
        if not r.is_ccw:
            for poly, holes in polygons:
                if poly.intersects(r):
                    holes.append(r)
                    break

    multipolygon = shapely.MultiPolygon([shapely.Polygon(poly.exterior, holes) for poly, holes in polygons])

    if not shapely.is_valid(multipolygon):
        print(shapely.validation.explain_validity(multipolygon))
        # assert False

    multipolygon = shapely.make_valid(multipolygon)
    if isinstance(multipolygon, shapely.Polygon):
        multipolygon = shapely.MultiPolygon([multipolygon])
    return multipolygon


def alpha_shape(points, alpha, strategy='circumcircle'):
    d = Delaunay(points)
    inc = simplex_inclusion(d, alpha, strategy)
    rings = trace_rings(d, inc)
    # alpha_shape = multipolygon_from_rings(rings)
    # Note: polygonize doesn't work in all cases (especially when using mean_edge_length method)
    alpha_shape = shapely.multipolygons(shapely.get_parts(shapely.polygonize(rings)))

    return SimpleNamespace(
        delaunay_triangulation=d,
        simplex_inclusion=inc,
        rings=rings,
        alpha_shape=alpha_shape)


def label_polygons(delaunay_triangulation, simplex_inclusion):
    inc = simplex_inclusion
    d = delaunay_triangulation

    labels = np.full(len(d.simplices), -1)
    n_polygons = 0
    for i in range(len(d.simplices)):
        if inc[i] and labels[i] == -1:
            q = [i]
            while len(q):
                x = q.pop()
                labels[x] = n_polyons
                for y in d.neighbors[x]:
                    if labels[y] == -1:
                        q.append(y)
            n_polygons += 1

    return n_polygons, labels

    # Would be interesting to compare speed with scipy connected components
    # e.g.
    # - Convert neighbors into list of edges
    # - Filter out edges to -1
    # - Filter out edges where either end is not included
    # - Convert edges to sparse array (csr_array)
    # - Call scipy.sparse.csgraph.connected_components


# Testing code:

def generate_point_clusters(clusters=10, points_per_cluster=200):
    n1 = clusters
    n2 = points_per_cluster
    c = np.random.random_sample((n1, 2)) * 20
    points = np.random.normal(c, 1, (n2, len(c), 2)).reshape((n1 * n2, 2))

    return points

def generate_donut_points(n):
    rad = np.random.normal(10, 1, n)
    theta = np.random.random_sample(n) * 2 * np.pi
    points = np.vstack([rad * np.cos(theta), rad * np.sin(theta)]).transpose()

    return points

def plot_alpha(alpha_info):
    d = alpha_info.delaunay_triangulation
    points = d.points
    inc = alpha_info.simplex_inclusion

    fig1, ax1 = plt.subplots()
    ax1.set_aspect('equal')
    ax1.tripcolor(points[:,0], points[:,1], inc, triangles=d.simplices)
    ax1.triplot(points[:,0], points[:,1], d.simplices, 'b-')

    for poly in alpha_info.alpha_shape.geoms:
        ax1.plot(*poly.exterior.xy)
        for hole in poly.interiors:
            ax1.plot(*hole.xy)

    fig1.show()


def test():
      np.random.seed(42)
      points = generate_point_clusters()
      # points = generate_donut_points(100000)
      alpha = alpha_shape(points, 2, 'circumcircle')
      plot_alpha(alpha)
      alpha = alpha_shape(points, 2, 'mean_edge_length')
      plot_alpha(alpha)

if __name__ == '__main__':
    test()
