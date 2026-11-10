"""Pure, testable movement model for the decorative hanging-silk behavior.

A hanging spider is allowed only beneath mature UPPER-corner webs. The lower
corner webs remain fully functional but never create a vertical dragline.
"""
from math import sin, pi


def clamp(v, a, b):
    return max(a, min(b, v))


def can_begin_hanging(corner, span, max_span, completed, threshold=0.84,
                      initial_span=215.0):
    """True only for large, complete, upper-corner webs."""
    if not completed or corner not in (0, 1):
        return False
    threshold = clamp(threshold, 0.25, 1.0)
    gap = max(0.0, max_span - initial_span)
    if gap < 1.0:
        return False
    return span >= initial_span + gap * threshold


def hanging_anchor(corner, span, screen_width, screen_height, canvas=580):
    """Choose an OUTER-edge attachment, away from the dense corner centre.

    The anchor remains inside the triangular footprint near the diagonal
    edge. Hanging will be visible in the open desktop area outside the web.
    """
    if corner not in (0, 1):
        raise ValueError('Bottom-corner webs do not support hanging.')
    from spider_nest import triangle_screen
    tip, x_edge, y_edge = triangle_screen(corner, span, screen_width,
                                          screen_height, canvas)
    # 0.64+0.34=.98: 2 percent inside diagonal edge, hence still part of web.
    return (tip[0] + (x_edge[0]-tip[0]) * 0.64,
            tip[1] + (y_edge[1]-tip[1]) * 0.34)


def hanging_depth(anchor_y, screen_height, half_window, spider_size):
    """End point well below the silk anchor while staying inside the monitor.

    The hanging motion must be clearly visible to a human observer: the spider
    should leave the web edge and descend into open desktop space, not merely
    extend a thread a short distance and appear stationary.
    """
    preferred = anchor_y + clamp(spider_size * 4.6, 175.0, 290.0)
    return clamp(preferred, anchor_y + 120.0, screen_height - half_window - 8.0)


def hanging_position(start, finish, t, sway=0.0):
    """Smooth rope descent/ascent; mild sideways sway only."""
    t = clamp(t, 0.0, 1.0)
    s = t * t * (3.0 - 2.0 * t)
    return (start[0] + (finish[0] - start[0]) * s + sway * sin(pi * t),
            start[1] + (finish[1] - start[1]) * s)


def drop_position(start, t, height, drift=0.0):
    """Release from silk with a short downward acceleration and side drift."""
    t = clamp(t, 0.0, 1.0)
    return start[0] + drift * t * t, start[1] + max(0., height) * t * t
