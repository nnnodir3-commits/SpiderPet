"""Screen-corner triangular silk retreat geometry and progressive area growth.
The triangular visual is a desktop adaptation; jumping spiders actually make
silk retreats rather than large prey-catching orb webs.
"""
import math

CANVAS_SIDE=580
INITIAL_SPAN=215.
MAX_AREA_RATIO=5.7

def corner_index(center,sw,sh):
    return (1 if center[0]>sw/2 else 0)+(2 if center[1]>sh/2 else 0)

def web_origin(corner,sw,sh,canvas=CANVAS_SIDE):
    return (0 if corner%2==0 else max(0,int(sw-canvas)),
            0 if corner<2 else max(0,int(sh-canvas)))

def max_web_span(sw,sh,canvas=CANVAS_SIDE):
    return max(INITIAL_SPAN,min(canvas-18.,sw*.48,sh*.75,INITIAL_SPAN*math.sqrt(MAX_AREA_RATIO)))

def grown_span(idle_duration, sw,sh, delay=34., expand_duration=105.):
    """Expand area up to ~5.7x over time (not 5.7x side length)."""
    progress=max(0.,min(1.,(idle_duration-delay)/max(.1,expand_duration)))
    smooth=progress*progress*(3-2*progress)
    return INITIAL_SPAN+(max_web_span(sw,sh)-INITIAL_SPAN)*smooth

def triangle_local(corner,span,canvas=CANVAS_SIDE):
    """One vertex at screen corner; two end vertices lie on adjacent screen edges."""
    left=(corner%2==0);top=(corner<2)
    tip_x=8. if left else canvas-8.
    tip_y=8. if top else canvas-8.
    sign_x=1. if left else -1.
    sign_y=1. if top else -1.
    edge=max(20.,min(canvas-17.,float(span)))-16.
    return ((tip_x,tip_y),(tip_x+sign_x*edge,tip_y),(tip_x,tip_y+sign_y*edge))

def triangle_screen(corner,span,sw,sh,canvas=CANVAS_SIDE):
    ox,oy=web_origin(corner,sw,sh,canvas)
    return tuple((ox+x,oy+y) for x,y in triangle_local(corner,span,canvas))

def point_in_triangle(p, triangle, tolerance=3.):
    """Check full triangular silk surface; tolerant to antialiased thin edges."""
    (x0,y0),(x1,y1),(x2,y2)=triangle
    dx1=x1-x0;dy1=y1-y0;dx2=x2-x0;dy2=y2-y0
    det=dx1*dy2-dx2*dy1
    if abs(det)<1.e-5:return False
    dx=p[0]-x0;dy=p[1]-y0
    u=(dx*dy2-dx2*dy)/det
    v=(dx1*dy-dx*dy1)/det
    eps=tolerance/max(1.,math.sqrt(abs(det)))
    return u>=-eps and v>=-eps and u+v<=1.+eps


def _quadratic(p0,p1,p2,steps=9):
    return tuple(((1-t)**2*p0[0]+2*(1-t)*t*p1[0]+t*t*p2[0],
                  (1-t)**2*p0[1]+2*(1-t)*t*p1[1]+t*t*p2[1])
                 for t in (j/steps for j in range(steps+1)))


def _between(a,b,f):
    return (a[0]+(b[0]-a[0])*f, a[1]+(b[1]-a[1])*f)


def silk_paths(corner,span,canvas=CANVAS_SIDE):
    """Natural, scalloped corner silk fan with no dense central pod.

    Returns tuples (points, width, role) where points are local pixel pairs.
    Unlike the old grid, cross threads sag inward in asymmetric scallops,
    radial guy lines are lightly bent, and the fringe has intentional gaps.
    The geometry stays within the original triangular clickable footprint.
    The shape is a decorative desktop motif, not an actual salticid prey web.
    """
    tip,left_anchor,bottom_anchor=triangle_local(corner,span,canvas)
    sign_x=1. if corner%2==0 else -1.
    sign_y=1. if corner<2 else -1.
    extent=abs(left_anchor[0]-tip[0])
    def coord(q):
        return (tip[0]+sign_x*q[0]*extent,
                tip[1]+sign_y*q[1]*extent)
    def mapped(path):return tuple(coord(p) for p in path)

    # Rather than a centered mathematical wheel, the convergence point is
    # shifted toward the corner like the irregular web in the reference.
    # Anchor the hub close to the resident's fixed corner retreat (about 87px
    # from both screen edges).  If the shelter grows fivefold, the heart of
    # the web must *not* drift away from the spider.
    hub=(min(.40,75.0/max(extent,1.0)),
         min(.40,75.0/max(extent,1.0)))
    A=(0.,0.);B=(1.,0.);C=(0.,1.)
    result=[]
    def put(path,width,role):
        result.append((mapped(path),width,role))

    # Long tension lines to the two screen edges, plus two uneven guide ropes.
    put((A,B),1.2,'anchor')
    put((A,C),1.2,'anchor')
    put((B,hub),1.65,'anchor')
    put((C,hub),1.65,'anchor')
    put((A,hub),1.45,'anchor')

    # Continuous edge anchors in perimeter order (clockwise from corner).
    # Unequal spacing removes the rigid grid and imitates hand-tensioned silk.
    anchors=[]
    for f in (.065,.145,.265,.425,.605,.80,1.):
        anchors.append((f,0.))
    for f in (.10,.24,.39,.55,.69,.84,.96):
        anchors.append((1.-f,f))
    for f in (.91,.73,.54,.36,.20,.075):
        anchors.append((0.,f))

    # Curved spokes, with a tiny reproducible bend that changes by direction.
    # All control points lie in the triangular region (convex combinations).
    for i,q in enumerate(anchors):
        midpoint=_between(hub,q,.50)
        left=anchors[(i-1)%len(anchors)]
        right=anchors[(i+1)%len(anchors)]
        wiggle=(math.sin(i*1.83)*.022)
        bend=(midpoint[0]+(right[0]-left[0])*wiggle,
              midpoint[1]+(right[1]-left[1])*wiggle)
        pts=_quadratic(hub,bend,q,12)
        put(pts,1.10 if i%6 else 1.5,'radial')

    # Scalloped spiral patches run between adjacent spokes; the midpoint sags
    # toward the hub so it feels organically tensioned, never rectangular.
    # Weave from the outside inward after the support spokes.
    levels=(.93,.825,.715,.605,.505,.415,.337,.267,.209,.160,.117)
    for ring, f in enumerate(levels):
        for i in range(len(anchors)):
            # Skip a few peripheral scallops, like a real imperfect web.
            if ring<2 and (i+2*ring)%13==0:
                continue
            aa=_between(hub, anchors[i], f*(1.+.018*math.sin(i*2.7+ring)))
            bb=_between(hub, anchors[(i+1)%len(anchors)],
                        f*(1.+.015*math.cos(i*1.7+ring*.8)))
            mid=_between(aa,bb,.5)
            sag=.11+(.035*math.sin(i*.81+ring*1.37))
            control=_between(mid,hub,sag)
            # 2 or 3 extra points inside the same curve make it soft at 15 mm.
            put(_quadratic(aa,control,bb,8),.96 if ring%3 else 1.10,'scallop')

    # A handful of extra short silk bridges near the central retreat.
    # These are not uniformly spaced: no square cell pattern forms.
    for i in range(0,len(anchors)-2,3):
        p=_between(hub, anchors[i],.125)
        q=_between(hub, anchors[i+2],.125)
        control=_between(_between(p,q,.5),hub,.21)
        put(_quadratic(p,control,q,8),.85,'inner')
    return result


def silk_segments(corner,span,canvas=CANVAS_SIDE):
    """Backwards-compatible thread fragments used by breakup animation/tests.

    One representative chord per curved strand avoids creating thousands of
    particles per animation tick when the large web gets destroyed.
    """
    return [(points[0],points[-1],round(width))
            for points,width,_ in silk_paths(corner,span,canvas)]
