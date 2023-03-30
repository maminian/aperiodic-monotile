from matplotlib import patches
import numpy as np
import os
import svg.path # python -m pip install svg.path

###

# SVG loading solution via https://stackoverflow.com/a/56913776

class Turtle_gen:
    def __init__(self, filename=None):
        from xml.dom import minidom

        if filename is None:
            filename = os.path.join( os.path.pardir, 'turtle-monotile.svg' )
            filename = os.path.abspath( filename ) # just in case
        #
        self.filename = filename

        
        doc = minidom.parse( self.filename )
        path_strings = [path.getAttribute('d') for path
                        in doc.getElementsByTagName('path')]
        doc.unlink()
        
        path = svg.path.parse_path( path_strings[0] )

        x,y = np.zeros( (2,len(path)) )

        for k,pi in enumerate(path[1:]):
            x[k+1] = pi.start.real
            y[k+1] = pi.start.imag
        #
        y = -y + max(y) # one weird trick
        
        # immutable copy
        self._sx = max(x) - min(x)
        self._sy = max(y) - min(y)
        self._x = tuple(x)
        self._y = tuple(y)
        self._z0 = self._x[0] + 1j*self._y[0]
        return
    
    def turtle_patch(self, x0=0., y0=0., rot=0, scale=1):
        '''
        Generates a matplotlib.patches.Patch() with the loaded 
        polygon anchored at the given cordinate with the 
        given scale and rotation.
        
        rotation done about self._x[0], self._y[0]
        rotation in degrees
        scale is a relative multiple (default: 1)
        '''
        z = np.array(self._x, dtype=complex) + 1j*np.array(self._y, dtype=complex)
        
        r = np.exp(1j*(rot*np.pi/180))
        # TODO: z0 as optional input
        z = r*(z - self._z0 ) + self._z0 
        z = z + x0 + 1j*y0
        patch = patches.Polygon( np.vstack([z.real, z.imag]).T )
        return patch

#############################


# demo script; else use the above code as an importable module
if __name__=="__main__": 
    from matplotlib import pyplot, collections
    pyplot.style.use('dark_background')

    np.random.seed(2718281828)
    grad = pyplot.cm.twilight
    #
    
    tg = Turtle_gen()
    
    tortles = []
    m,n = 5,5
    for k in range(m*n):
        i,j = int(k//n), k%n
        
        tortle = tg.turtle_patch(
            x0 = i*tg._sx,
            y0 = j*tg._sy
        )
        s = np.random.uniform(0,1) # I don't know, whatever
        tortle.set_facecolor( grad( s ) )
        tortle.set_edgecolor( grad((s+0.5)%1) )
        tortle.set_linewidth(2)
        tortle.set_hatch(np.random.choice(['x','/','\\']))
        tortles.append( tortle )


    coll = collections.PatchCollection(tortles, match_original=True)

    fig,ax = pyplot.subplots(
        constrained_layout=True, 
        figsize=(tg._sx, tg._sy)
    )
    ax.add_collection(coll)

    # why doesn't pyplot auto-update
    ax.set_xlim([0,(i+1)*tg._sx])
    ax.set_ylim([0,(i+1)*tg._sy])
    # polish and hide plotting doodads
    ax.set_aspect('equal')
    ax.set_xticks([])
    ax.set_yticks([])
    for v in ax.spines.values():
        v.set_visible(False)

    if False:
        fig.savefig('tortles.png', bbox_inches='tight')
    fig.show()
    

