"""Win32 visible window outline tracking; geometry functions are pure/testable."""
import ctypes, math, os
from ctypes import wintypes


def nearest_border(rect,x,y):
    left,top,right,bottom=rect
    return min(((max(left,min(right,x)),top,0),
                (right,max(top,min(bottom,y)),1),
                (max(left,min(right,x)),bottom,2),
                (left,max(top,min(bottom,y)),3)),
               key=lambda item:(item[0]-x)**2+(item[1]-y)**2)


def patrol_route(rect,x,y,clockwise=True,rounds=1):
    px,py,side=nearest_border(rect,x,y)
    left,top,right,bottom=rect
    if clockwise:
        corners=((right,top),(right,bottom),(left,bottom),(left,top))
    else:
        corners=((left,top),(right,top),(right,bottom),(left,bottom))
    # Side numbers are top/right/bottom/left. Clockwise next corners follow this order.
    result=[(px,py)]
    for i in range(rounds*4+1):
        j=(side+i)%4 if clockwise else (side-i)%4
        pt=corners[j]
        if pt!=result[-1]:result.append(pt)
    return result


def visible_windows(excluded=(),screen_size=None):
    if os.name != 'nt': return []
    user32=ctypes.windll.user32
    try:dwm=ctypes.windll.dwmapi
    except (AttributeError,OSError):dwm=None
    ignored={int(v) for v in excluded}
    found=[]
    try:
        user32.EnumWindows.argtypes=[ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM),wintypes.LPARAM]
        user32.EnumWindows.restype=wintypes.BOOL
        user32.GetWindowRect.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.RECT)]
        user32.GetWindowRect.restype=wintypes.BOOL
        user32.GetWindowThreadProcessId.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]
        user32.GetWindowTextLengthW.argtypes=[wintypes.HWND]
        user32.GetWindowTextLengthW.restype=ctypes.c_int
        user32.IsWindowVisible.argtypes=[wintypes.HWND]
        user32.IsWindowVisible.restype=wintypes.BOOL
        user32.IsIconic.argtypes=[wintypes.HWND]
        user32.IsIconic.restype=wintypes.BOOL
        if dwm:
            dwm.DwmGetWindowAttribute.argtypes=[wintypes.HWND,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD]
            dwm.DwmGetWindowAttribute.restype=wintypes.LONG
    except (AttributeError,TypeError):return []
    callback_type=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
    sw,sh=screen_size if screen_size else (user32.GetSystemMetrics(0),user32.GetSystemMetrics(1))
    own_pid=os.getpid()
    def visit(hwnd,_):
        if int(hwnd) in ignored or not user32.IsWindowVisible(hwnd) or user32.IsIconic(hwnd):return True
        if user32.GetWindowTextLengthW(hwnd)==0:return True
        proc=wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd,ctypes.byref(proc))
        if proc.value==own_pid:return True
        r=wintypes.RECT()
        if not user32.GetWindowRect(hwnd,ctypes.byref(r)):return True
        if dwm:
            rr=wintypes.RECT()
            try:
                if dwm.DwmGetWindowAttribute(hwnd,9,ctypes.byref(rr),ctypes.sizeof(rr))==0:
                    r=rr
                cloak=wintypes.DWORD()
                if dwm.DwmGetWindowAttribute(hwnd,14,ctypes.byref(cloak),ctypes.sizeof(cloak))==0 and cloak.value:
                    return True
            except (OSError,AttributeError):pass
        a,b,c,d=int(r.left),int(r.top),int(r.right),int(r.bottom)
        if c-a<170 or d-b<115:return True
        if c<=0 or d<=0 or a>=sw or b>=sh:return True
        # Only the visible portion of the primary screen can be patrolled.
        a=max(a,8);b=max(b,8);c=min(c,sw-8);d=min(d,sh-8)
        if c-a<125 or d-b<90:return True
        found.append((int(hwnd),(a,b,c,d)))
        return True
    cb=callback_type(visit)
    try:user32.EnumWindows(cb,0)
    except (OSError,ValueError):return []
    return found


def choose_nearby_window(windows,x,y,margin,limit=340):
    ranked=[]
    for hwnd,rect in windows:
        a,b,c,d=rect
        inset=(max(margin,a),max(margin,b),min(c,1e9),min(d,1e9))
        if inset[2]-inset[0]<90 or inset[3]-inset[1]<60:continue
        px,py,_=nearest_border(rect,x,y)
        dist=math.hypot(px-x,py-y)
        if dist<=limit:ranked.append((dist,hwnd,rect))
    return min(ranked,key=lambda v:v[0]) if ranked else None
