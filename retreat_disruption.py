"""Pure geometry and timing for destroyable SpiderPet silk retreats."""
import math


def cursor_in_retreat(cursor, center, radius_x=68., radius_y=63.):
    """True when the global cursor is over the occupied retreat's drawn centre."""
    if center is None:
        return False
    rx=max(1.,float(radius_x)); ry=max(1.,float(radius_y))
    dx=(float(cursor[0])-center[0])/rx
    dy=(float(cursor[1])-center[1])/ry
    return dx*dx+dy*dy <= 1.


class DisruptionClock:
    """Prevent immediate replacement of a silk retreat after its destruction."""
    def __init__(self):
        self.rebuild_after=0.
        self.last_destroyed_at=None

    def trigger(self,now,rebuild_delay=120.):
        self.last_destroyed_at=float(now)
        self.rebuild_after=max(self.rebuild_after,float(now)+max(1.,float(rebuild_delay)))

    def can_rebuild(self,now):
        return float(now)>=self.rebuild_after
