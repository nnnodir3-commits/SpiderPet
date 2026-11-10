"""Deterministic synchronized two-instance salticid contest choreography."""
import hashlib, math

DUEL_DURATION=7.25
BEATS=(
    (0.00,0.72,'display',-1),
    (0.72,1.52,'strike',0),
    (1.52,1.88,'recover',-1),
    (1.88,2.68,'strike',1),
    (2.68,3.03,'recover',-1),
    (3.03,3.83,'strike',0),
    (3.83,4.18,'recover',-1),
    (4.18,4.98,'strike',1),
    (4.98,5.25,'recover',-1),
    (5.25,6.10,'strike',2),
    (6.10,6.30,'recover',-1),
    (6.30,7.25,'finisher',2),
)

def winner_role(id_a,id_b):
    """Role 0/1 computed identically in either process; not always the same spider."""
    pair='|'.join(sorted((str(id_a),str(id_b))))
    return hashlib.sha256(pair.encode('ascii')).digest()[0]&1

def duel_phase(elapsed,my_role,winner):
    """Return phase, am_attacking, normalized progress from both participants' clock."""
    if elapsed<0:return ('display',False,0.)
    for start,end,name,attacker in BEATS:
        if elapsed<end:
            actual=winner if attacker==2 else attacker
            return (name, actual==my_role, max(0.,(elapsed-start)/(end-start)))
    return ('finish',False,1.)

def escape_destination(position, enemy, screen, margin, distance=480.):
    """Choose a long retreat directed predominantly away from the opponent."""
    x,y=position;ex,ey=enemy;sw,sh=screen
    dx=x-ex;dy=y-ey
    angle=math.atan2(dy,dx) if dx*dx+dy*dy>1 else math.pi/3
    candidates=[]
    base_distance=math.hypot(x-ex,y-ey)
    for j in range(24):
        a=angle+j*math.tau/24
        tx=max(margin,min(sw-margin,x+math.cos(a)*distance))
        ty=max(margin,min(sh-margin,y+math.sin(a)*distance))
        travelled=math.hypot(tx-x,ty-y)
        enemy_distance=math.hypot(tx-ex,ty-ey)
        # Penalize paths that cut through the victor's position.
        dx2=tx-x;dy2=ty-y
        t=max(0.,min(1.,((ex-x)*dx2+(ey-y)*dy2)/max(1.,dx2*dx2+dy2*dy2)))
        clearance=math.hypot(x+t*dx2-ex,y+t*dy2-ey)
        penalty=max(0.,min(70.,base_distance*.85)-clearance)*5.
        score=enemy_distance+.17*travelled-penalty
        candidates.append((score,tx,ty))
    _,tx,ty=max(candidates)
    return tx,ty


def foot_contact_clearance(size,other_size):
    """Forelegs overlap slightly at impact; bodies stay apart (in pixels)."""
    return 0.52*(float(size)+float(other_size))/2.


def strike_motion(position, anchor, opponent, size, opponent_size, attacking, progress, finisher=False):
    """(target, speed) synchronized lunge and recoil for a live two-process duel.

    Defending actor holds its ground until the attacking forelegs reach contact.
    Only then does the apparent impact push the defender backwards. Keeping this
    delay is critical: the earlier implementation moved the target away too soon.
    """
    import math
    x,y=position;ax,ay=anchor;ex,ey=opponent
    dx=ex-x;dy=ey-y
    d=max(1.,math.hypot(dx,dy));ux,uy=dx/d,dy/d
    p=max(0.,min(1.,progress))
    if attacking:
        if p<.14:
            return ((ax-ux*size*.25,ay-uy*size*.25),220.)
        if p<.68:
            gap=foot_contact_clearance(size,opponent_size)
            # Accelerate toward the actual opponent rather than an old anchor.
            return ((ex-ux*gap,ey-uy*gap),1100. if finisher else 900.)
        return ((ax,ay),510. if finisher else 430.)
    # Defender stays in place as the first blow arrives, then is pushed back.
    if p<.62:return ((ax,ay),0.)
    if p<.84:
        recoil=size*(1.45 if finisher else 1.05)
        return ((ax-ux*recoil,ay-uy*recoil),640. if finisher else 560.)
    return ((x,y),0.) if finisher else ((ax,ay),275.)


def gait_cycle_distance(size, speed, combat=False):
    """Pixels traveled for one complete leg-step cycle; scales with body speed.

    At 50-70px/sec a cycle is about 0.80 body lengths (was 1.32). During
    sprints, the stride becomes somewhat longer to avoid strobing fast feet.
    """
    speed=max(0.,float(speed))
    # A 32-frame 8-leg cycle every ~0.78-1.00 apparent body length. The old
    # 1.32-1.55 body-length cycle looked like foot sliding at 50-75 px/s.
    # An adaptive, slightly longer stride under rapid sprint avoids strobing.
    if combat:
        factor=0.73+min(speed,1100.)*.00016
    else:
        factor=0.80+min(max(0.,speed-65.),300.)*.00055
    return max(1.,float(size)*factor)
