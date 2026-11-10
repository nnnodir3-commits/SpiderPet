"""Deterministic helpers for periodic excursions from a silk retreat.

All durations are deliberately stylized animation parameters, not biological measurements.
"""
import math
import random


def departure_waypoint(den, width, height, margin, vicinity_radius,
                       jitter=0.0, excursion=255.0):
    """Aim away from the corner den and into the screen, not at the nearby wall."""
    cx,cy=width*.5,height*.5
    a=math.atan2(cy-den[1],cx-den[0])+jitter
    r=max(float(vicinity_radius)+95., float(excursion))
    x=max(margin,min(width-margin,den[0]+math.cos(a)*r))
    y=max(margin,min(height-margin,den[1]+math.sin(a)*r))
    # Prefer the center if a very small screen makes the waypoint too close.
    if math.hypot(x-den[0],y-den[1])<vicinity_radius+35:
        x=max(margin,min(width-margin,cx))
        y=max(margin,min(height-margin,cy))
    return x,y


def retreat_is_due(now, last_interest, idle_after, blocked_until):
    return now>=blocked_until and now-last_interest>idle_after
