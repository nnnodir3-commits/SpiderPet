"""Pure natural idle reactions and pre-duel threat choreography for SpiderPet v38."""
import math

def clamp(x,lo,hi):
    return max(lo,min(hi,x))

def observe_rotation(initial, elapsed, duration, amplitude=0.62):
    """Look left, centre, right, centre without moving the spider's feet."""
    p=clamp(elapsed/max(duration,1.e-6),0.,1.)
    return initial+amplitude*math.sin(2.*math.pi*p)

def probe_frame(elapsed):
    """Front-leg micro steps using original rigid, unmodified photo poses."""
    cycle=(0,2,5,8,6,3,1,0,1,3,6,4,2,0)
    return cycle[int(max(0.,elapsed)*12.)%len(cycle)]

def threat_frame(elapsed, phase_seconds=3.15):
    """12 alternating raised-foreleg silhouettes, held high before impact."""
    p=clamp(elapsed/max(phase_seconds,1.e-6),0.,.999999)
    return min(11,int(p*12.))

def retreat_backstep(start, danger, size, bounds):
    """Move away while maintaining face-to-danger attitude, stay on monitor."""
    x,y=start;mx,my=danger;w,h=bounds
    dx=x-mx;dy=y-my
    d=math.hypot(dx,dy)
    if d<1.: dx,dy,d=-1.,-.45,math.hypot(1.,.45)
    shift=clamp(size*.90,27.,64.)
    margin=max(30.,size*.75)
    return (clamp(x+dx/d*shift,margin,max(margin,w-margin)),
            clamp(y+dy/d*shift,margin,max(margin,h-margin)))

def threat_display_motion(anchor,opponent,size,role,progress):
    """Small approach and sideways sway; NO collision before the actual duel.

    The original strike stage and pre-existing winner/loser logic remain intact.
    """
    x,y=anchor;ox,oy=opponent
    dx=ox-x;dy=oy-y;dist=math.hypot(dx,dy)
    if dist<1.:dx,dy,dist=1.,0.,1.
    ux,uy=dx/dist,dy/dist
    p=clamp(progress,0.,1.)
    # Raised-arm phase begins stationary. Approach gently, then ease back.
    ramp=math.sin(math.pi*clamp((p-.10)/.90,0.,1.))**2
    ahead=min(size*.36,max(0.,dist-size*1.10)*.18)*ramp
    lateral=math.sin(p*math.tau*2.0)*size*.075*ramp*(1 if role else -1)
    return (x+ux*ahead-uy*lateral,y+uy*ahead+ux*lateral)
