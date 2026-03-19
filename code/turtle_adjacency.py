# Current goal: read in an SVG of polygons and construct an adjacency graph
# "rook rules" (meaning: don't connect corners).

#
# See https://networkx.org/documentation/stable/auto_examples/geospatial/plot_polygons.html 

from libpysal import weights
import networkx as nx
import svg.path
import numpy as np

class PolygonXY:
    def __init__(self,x,y):
        self.x = x
        self.y = y
        self._sx = max(x) - min(x)
        self._sy = max(y) - min(y)
        self._x = tuple(x)
        self._y = tuple(y)
        self._z0 = self._x[0] + 1j*self._y[0]
        return
    
    def patch(self, x=None, y=None, x0=0., y0=0., rot=0, scale=1, ax=None, pc=None):
        '''
        Generates a matplotlib.patches.Patch() with the loaded 
        polygon anchored at the given cordinate with the 
        given scale and rotation.
        
        rotation done about self._x[0], self._y[0]
        rotation in degrees
        scale is a relative multiple (default: 1)
        
        If ax is not None, the patch is inserted in the pyplot Axes.
        '''
        from matplotlib import patches
        
        z = np.array(self._x, dtype=complex) + 1j*np.array(self._y, dtype=complex)
        
        r = np.exp(1j*(rot*np.pi/180))
        # TODO: z0 as optional input
        z = r*(z - self._z0 ) + self._z0 
        z = z + x0 + 1j*y0
        if pc is None:
            pc = np.random.uniform(0,1)
        cc = plt.cm.cividis(pc)
        cc = list(cc)
        cc[3] = 0.5
        patch = patches.Polygon( np.vstack([z.real, z.imag]).T, facecolor=cc, edgecolor='w')
        if ax is not None:
        #    ax.add_patch(patch)
            ax.fill(z.real, z.imag, facecolor=cc, edgecolor='w')
        return patch
#

def polygons_from_svg_path(filename=None):
    from xml.dom import minidom
    import os

    if filename is None:
        filename = os.path.join( os.path.pardir, 'turtle-monotile.svg' )
        filename = os.path.abspath( filename ) # just in case
    #

    
    doc = minidom.parse( filename )
    path_strings = [path.getAttribute('d') for path
                    in doc.getElementsByTagName('path')]
    doc.unlink()
    
    polygons = []
    for j in range(len(path_strings)):
        path = svg.path.parse_path( path_strings[0] )

        x,y = np.zeros( (2,len(path)) )

        for k,pi in enumerate(path[1:]):
            x[k+1] = pi.start.real
            y[k+1] = pi.start.imag
        #
        y = -y + max(y) # one weird trick
        polygons.append(PolygonXY(x,y))
    #
    
    return polygons
#


def polygons_from_svg_polygons(filename=None):
    from xml.dom import minidom
    import os

    if filename is None:
        filename = os.path.join( os.path.pardir, 'turtle-monotile.svg' )
        filename = os.path.abspath( filename ) # just in case
    #
    
    doc = minidom.parse( filename )
    path_strings = [poly.attributes['points'].value for poly
                    in doc.getElementsByTagName('polygon')]
    doc.unlink()
    
    polygons = []
    for ss in path_strings:
        #path = svg.path.parse_path( path_strings[0] )
        coords = np.array([[float(z) for z in row.split(',')] for row in ss.split(' ')]).T

        polygons.append(PolygonXY(coords[0], coords[1]))
    #
    
    return polygons
#



# Right now, the svg file must come as an export from this page:
# https://cs.uwaterloo.ca/~csk/hat/h7h8.html
tu = polygons_from_svg_polygons('tort2.svg')

#############
from matplotlib import pyplot as plt

fig,ax = plt.subplots(figsize=(6,6), constrained_layout=True)
for i,p in enumerate(tu):
    p.patch(ax=ax, pc=i/(len(tu)-1))

ax.set(aspect='equal')

#########
import shapely
from libpysal import graph
import geopandas

polys = [shapely.Polygon(zip(p.x,p.y)) for p in tu]
#poly_shapes = weights.Queen.from_iterable(polys)
guh = geopandas.GeoSeries(polys)

# March 18 6pm: neither solution works; fuzzy_contiguity still 
# connecting corner intersections at 0 tolerance;
# "strict" contiguity fails with an overlap error if by_perimeter=True;
# produces junk if set to False.
# consult:
# ~/.local/lib/python3.12/site-packages/libpysal/graph/_contiguity.py:202

#poly_shapes = graph.Graph.build_contiguity(guh, by_perimeter=False, rook=True, strict=False)
poly_shapes = graph.Graph.build_fuzzy_contiguity(polys, buffer=1e-8)
G = poly_shapes.to_networkx()

pos = [np.array(p.centroid.xy).flatten() for p in polys]
nx.draw_networkx(G,pos=pos,ax=ax)

fig.savefig('turt_adjacency.png', bbox_inches='tight')
fig.show()    
plt.ion()
