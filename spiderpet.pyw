# SpiderPet v38 — natural behavior + pre-combat foreleg display on stable v36
# Photoreal v15 sprites with enlarged alternating leg sweeps. Ctrl+Shift+Q exits.
import ctypes, math, random, sys, time, traceback, os, tempfile
from pathlib import Path
import tkinter as tk
from PIL import Image, ImageTk
from retreat_lifecycle import RetreatLifecycle
from retreat_activity import departure_waypoint, retreat_is_due
from retreat_disruption import cursor_in_retreat, DisruptionClock
from spider_windows import visible_windows,choose_nearby_window,patrol_route
from spider_peers import PeerRegistry
from spider_activity import (observe_rotation,probe_frame,threat_frame,
                             retreat_backstep,threat_display_motion)
from spider_combat import (DUEL_DURATION, duel_phase, winner_role, escape_destination,
                           strike_motion, foot_contact_clearance, gait_cycle_distance)
from spider_hanging import (can_begin_hanging, hanging_anchor as calculate_hanging_anchor,
                            hanging_depth, hanging_position, drop_position)
from spider_nest import (CANVAS_SIDE, INITIAL_SPAN, corner_index, web_origin,
                         grown_span, triangle_screen, point_in_triangle, silk_segments, silk_paths, max_web_span)

BASE=Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
# Errors are written in a writable per-user location even when the EXE is on
# Desktop, a network drive, or Program Files. This works for one-file builds.
LOG=Path(os.environ.get('LOCALAPPDATA') or tempfile.gettempdir())/'SpiderPet'/'spiderpet_error.log'

def show_error(message):
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open('a', encoding='utf-8') as f:
            f.write('\n===== SpiderPet diagnostic '+time.strftime('%Y-%m-%d %H:%M:%S')+' =====\n')
            f.write(message+'\n')
    except Exception:
        pass
    try:
        ctypes.windll.user32.MessageBoxW(
            None,
            'SpiderPet ishga tushmadi. Xatolik tafsiloti:\n'+str(LOG)+
            '\n\nOynani yopib, log faylini yuboring.',
            'SpiderPet — XATOLIK', 0x10)
    except Exception:
        pass
    try:
        if sys.stderr: sys.stderr.write(message+'\n')
    except Exception:
        pass

PI=math.pi

def clamp(v,a,b):return max(a,min(b,v))
def angle_diff(a,b):return (a-b+PI)%(2*PI)-PI

def main():
    user32=ctypes.windll.user32
    try:user32.SetProcessDPIAware()
    except Exception:pass
    dpi=user32.GetDpiForSystem() if hasattr(user32,'GetDpiForSystem') else 96
    size=clamp(int(os.environ.get('SPIDER_SIZE_PX',round(15*dpi/25.4))),24,180)
    side=max(150,size+90);key='#ff00ff'
    root=tk.Tk();root.report_callback_exception=lambda et,ev,tb: show_error(''.join(traceback.format_exception(et,ev,tb)));root.overrideredirect(True);root.attributes('-topmost',True)
    root.configure(bg=key);root.wm_attributes('-transparentcolor',key)
    sw=user32.GetSystemMetrics(0);sh=user32.GetSystemMetrics(1)
    # Different initial coordinates allow two independently launched copies to
    # explore separately; test mode can place them deliberately close together.
    start_x=float(os.environ.get('SPIDER_START_X_FRAC',random.uniform(.30,.62)))
    start_y=float(os.environ.get('SPIDER_START_Y_FRAC',random.uniform(.27,.60)))
    x=sw*clamp(start_x,.10,.90);y=sh*clamp(start_y,.10,.90);heading=PI/2
    root.geometry(f'{side}x{side}+{round(x-side/2)}+{round(y-side/2)}')
    canvas=tk.Canvas(root,width=side,height=side,bg=key,highlightthickness=0,bd=0);canvas.pack()
    # Ordered alpha coverage: true RGB foreground with no purple colorkey fringe.
    bayer=((0,8,2,10),(12,4,14,6),(3,11,1,9),(15,7,13,5))
    def keyed(sprite):
        # PhotoImage only needs to contain the spider, not the transparent 150px
        # Tk window. This reduces memory for two independent running instances.
        im=Image.new('RGB',(size,size),(255,0,255));inp=sprite.load();out=im.load()
        for iy in range(size):
            for ix in range(size):
                r,g,b,a=inp[ix,iy]
                if a>(bayer[iy&3][ix&3]+.5)*16:
                    if r>245 and b>245 and g<12:r=244
                    out[ix,iy]=(r,g,b)
        return ImageTk.PhotoImage(im)
    # V32: 32 authentic *unwarped* poses x 24 directions. Do not interpolate
    # different leg silhouettes with Image.blend: crossfading two paws creates
    # ghost limbs, and the former regional remapping bent the front-left leg.
    # Phase is still tracked with 128 subdivisions for speed-proportional cadence;
    # the rendered frame is the nearest actual (non-deformed) pose.
    # Rendering at ~1.75 screen size first preserves fine hairs after rotation.
    render_size=max(size,round(size*1.75))
    sprites=[Image.open(BASE/f'walk_{i:02d}.png').convert('RGBA').resize(
             (render_size,render_size),Image.Resampling.LANCZOS) for i in range(32)]
    frames=[]
    for sprite in sprites:
        rotset=[]
        for direction in range(24):
            r=sprite.rotate(direction*15,Image.Resampling.BICUBIC,expand=False)
            r=r.resize((size,size),Image.Resampling.LANCZOS)
            rotset.append(keyed(r))
        frames.append(rotset)
    # Only generate jump visual sizes for the neutral (no gait) pose.
    jumps=[]
    for factor in (1.04,1.11,1.17):
        direction_set=[]
        for direction in range(24):
            r=sprites[0].rotate(direction*15,Image.Resampling.BICUBIC,expand=False)
            expanded=r.resize((max(1,round(size*factor)),)*2,Image.Resampling.LANCZOS)
            base=Image.new('RGBA',(size,size),(0,0,0,0))
            base.alpha_composite(expanded,((size-expanded.width)//2,(size-expanded.height)//2))
            direction_set.append(keyed(base))
        jumps.append(direction_set)
    # V38 raised threat pose: two real textured forelegs, rigidly rotated at
    # their roots offline (never warp the abdomen, head, or foreleg length).
    threat=[]
    for i in range(12):
        sprite=Image.open(BASE/f'threat_{i:02d}.png').convert('RGBA').resize(
            (render_size,render_size),Image.Resampling.LANCZOS)
        threat.append([keyed(sprite.rotate(direction*15,Image.Resampling.BICUBIC,expand=False)
                         .resize((size,size),Image.Resampling.LANCZOS))
                       for direction in range(24)])
    # Silk shelter: drawn on a separate click-through overlay near screen edge.
    # A salticid builds a silk retreat, not an orb prey-catching web.
    silk=tk.Toplevel(root);silk.overrideredirect(True);silk.attributes('-topmost',True)
    silk.configure(bg=key);silk.wm_attributes('-transparentcolor',key)
    websize=CANVAS_SIDE
    webcanvas=tk.Canvas(silk,width=websize,height=websize,bg=key,highlightthickness=0,bd=0)
    webcanvas.pack()
    silk.withdraw()
    # During hanging the spider and the silk MUST be drawn on the SAME
    # click-through Tk toplevel. Earlier versions drew the spider in `root`
    # and only the strand in `cord`. Their z-order could diverge on Windows:
    # the user saw a strand getting longer while the spider looked stationary.
    # We instead hide the original sprite and draw the identical cached spider
    # PhotoImage inside the moving rope overlay at the actual body coordinates.
    cord=tk.Toplevel(root);cord.overrideredirect(True);cord.attributes('-topmost',True)
    cord.configure(bg=key);cord.wm_attributes('-transparentcolor',key)
    cord_width=max(side,round(size*2.2))
    cordcanvas=tk.Canvas(cord,width=cord_width,height=12,bg=key,
                         highlightthickness=0,bd=0);cordcanvas.pack()
    cord.withdraw()
    cord_shown=False
    def hide_cord():
        nonlocal cord_shown
        if cord_shown:
            cord.withdraw()
            cord_shown=False
        # Re-enable the regular spider only after finishing the rope movement.
        canvas.itemconfigure(item,state='normal')
    web_lines=[];web_visible=False;web_corner=None
    # The shelter expires only after the spider has truly left it for five minutes.
    # Optional env overrides provide a quick test without changing real defaults.
    idle_after=float(os.environ.get('SPIDER_RETREAT_IDLE_SEC','18'))
    abandonment_after=float(os.environ.get('SPIDER_RETREAT_ABANDON_SEC','300'))
    fade_seconds=float(os.environ.get('SPIDER_RETREAT_FADE_SEC','30'))
    home=RetreatLifecycle(abandon_after=abandonment_after, fade_seconds=fade_seconds,
                          vicinity_radius=max(72.,size*1.3))
    shown_fade_step=40
    nest_span=INITIAL_SPAN
    nest_calm_since=0.
    nest_ready_at=0.
    nest_render_stamp=0.
    nest_render_span=-1.
    nest_corner=0
    nest_growth_delay=float(os.environ.get('SPIDER_NEST_GROW_DELAY_SEC','34'))
    nest_growth_seconds=float(os.environ.get('SPIDER_NEST_GROW_SECONDS','105'))
    # Hanging is deliberately restricted to TOP-CORNER large webs; lower
    # corners can build and expand normally but never hang a spider.
    hang_min_web_ratio=float(os.environ.get('SPIDER_HANG_WEB_RATIO','.84'))
    hang_descend_seconds=max(.2,float(os.environ.get('SPIDER_HANG_DESCEND_SEC','1.45')))
    hang_ascend_seconds=max(.2,float(os.environ.get('SPIDER_HANG_ASCEND_SEC','1.28')))
    hang_dwell_min=max(.5,float(os.environ.get('SPIDER_HANG_DWELL_MIN_SEC','3.5')))
    hang_dwell_max=max(hang_dwell_min,float(os.environ.get('SPIDER_HANG_DWELL_MAX_SEC','6.0')))
    hang_repeat_min=max(1.,float(os.environ.get('SPIDER_HANG_REPEAT_MIN_SEC','25')))
    hang_repeat_max=max(hang_repeat_min,float(os.environ.get('SPIDER_HANG_REPEAT_MAX_SEC','47')))
    hang_next_allowed=0.
    hang_started=0.
    hang_begin=(0.,0.)  # current segment start (descend or ascend)
    hang_end=(0.,0.)
    hang_anchor=(0.,0.)
    hang_top=(0.,0.)    # visible body position right under the web edge
    hang_drop_start=0.
    hang_drop_end=0.
    hang_drop_begin=(0.,0.)
    hang_drop_dx=0.
    hang_drop_height=0.
    hang_rest_started=0.
    hang_trace_at=0.

    # A den is removed immediately in the behavioural model; its broken fibres
    # fall away for a short visual effect. Rebuilding is postponed after a loss.
    disruption=DisruptionClock()
    ruin_start=0.
    ruin_seconds=.82
    anger_until=0.
    anger_strikes=0
    # The old version ended after three strikes, often after only a few seconds.
    anger_max_strikes=int(os.environ.get('SPIDER_RAGE_MAX_STRIKES','6'))
    anger_duration_min=float(os.environ.get('SPIDER_RAGE_MIN_SEC','17'))
    anger_duration_max=float(os.environ.get('SPIDER_RAGE_MAX_SEC','22'))
    anger_next_strike=0.
    anger_point=(x,y)
    anger_backoff=(x,y)
    anger_rear_start=0.
    anger_rear_from=(x,y)
    anger_rear_end=0.
    # Once resting has completed, the spider MUST leave the den to forage.
    # The absence of a cursor is not a reason to return immediately.
    den_rest_min=max(1.,float(os.environ.get('SPIDER_DEN_REST_MIN_SEC','9')))
    den_rest_max=max(den_rest_min,float(os.environ.get('SPIDER_DEN_REST_MAX_SEC','16')))
    forage_cooldown_min=max(8.,float(os.environ.get('SPIDER_FORAGE_MIN_SEC','55')))
    forage_cooldown_max=max(forage_cooldown_min,float(os.environ.get('SPIDER_FORAGE_MAX_SEC','85')))
    def den_rest_duration():
        return random.uniform(den_rest_min,den_rest_max)

    def silk_geometry(cx,cy):
        nonlocal nest_corner
        nest_corner=corner_index((cx,cy),sw,sh)
        ox,oy=web_origin(nest_corner,sw,sh,websize)
        silk.geometry(f'{websize}x{websize}+{ox}+{oy}')

    def draw_silk(progress):
        nonlocal shown_fade_step,nest_render_span
        webcanvas.delete('all')
        shown_fade_step=40
        nest_render_span=nest_span
        strands=silk_paths(nest_corner,nest_span,websize)
        count=round(len(strands)*clamp(progress,0.,1.))
        # Curved strands are drawn as smoothly sampled polylines, not straight
        # chords. A dark fine under-stroke makes them visible on white desktops;
        # silver highlights remain visible on dark desktops.
        for i,(points,width,role) in enumerate(strands[:count]):
            flat=[v for p in points for v in p]
            if role=='anchor':
                ink='#b9b6c3';stroke=2
            elif role=='radial':
                ink='#c5c2cd' if i%3 else '#e3e0e7';stroke=1
            elif role=='inner':
                ink='#f0edf3';stroke=1
            else:
                ink='#d1cfda' if (i%7) else '#eeebf2';stroke=1
            # Duplicate very faint dark edge instead of opaque fake background.
            webcanvas.create_line(*flat,fill='#66646e',width=stroke+1,
                                  joinstyle=tk.ROUND,capstyle=tk.ROUND)
            webcanvas.create_line(*flat,fill=ink,width=stroke,
                                  joinstyle=tk.ROUND,capstyle=tk.ROUND)
        # No dense central pod. Keep only the curved, lightweight silk threads.

    def draw_broken_silk(progress):
        """Scale broken filaments to the entire expanded triangular shelter."""
        webcanvas.delete('all')
        p=clamp(progress,0.,1.)
        segments=silk_segments(nest_corner,nest_span,websize)
        tip=segments[0][0]
        for i,(a,b,width) in enumerate(segments[::2]):
            if p>.65+(i%8)*.041:continue
            mid=((a[0]+b[0])*.5,(a[1]+b[1])*.5)
            theta=i*2.39996323
            driftx=math.cos(theta)*p*(10.+i%5*6)
            drifty=math.sin(theta)*p*(9.+i%4*4)+32.*p*p
            remain=max(.04,1.-p*.78)
            half=min(20.,math.hypot(a[0]-b[0],a[1]-b[1])*.18)*remain
            ca=math.cos(theta+.4);sa=math.sin(theta+.4)
            webcanvas.create_line(mid[0]+driftx-ca*half,mid[1]+drifty-sa*half,
                                  mid[0]+driftx+ca*half,mid[1]+drifty+sa*half,
                                  fill=('#efedf4' if i%3==0 else '#b9b5c4'),width=1)

    def set_silk_opacity(opacity):
        # Tk transparent-colour windows do not support ordinary per-item alpha.
        # Instead ordered thinning + native stipple makes strands fade transparently,
        # without mixing purple colour-key pixels into their edges.
        nonlocal shown_fade_step
        level=round(clamp(opacity,0.,1.)*40.)
        if level==shown_fade_step:
            return
        shown_fade_step=level
        a=level/40.
        items=webcanvas.find_all()
        for idx,item_id in enumerate(items):
            # Stable pseudo-random erasure order prevents the web shrinking linearly.
            threshold=(((idx*37+11)%101)/101.)*.25
            if a<=0 or a<threshold:
                webcanvas.itemconfigure(item_id,state='hidden')
                continue
            kind=webcanvas.type(item_id)
            stipple='' if a>.82 else ('gray75' if a>.61 else ('gray50' if a>.38 else ('gray25' if a>.17 else 'gray12')))
            if kind=='line':
                webcanvas.itemconfigure(item_id,state='normal',stipple=stipple)
            elif kind in ('oval','polygon'):
                webcanvas.itemconfigure(item_id,state='normal',outlinestipple=stipple)
            else:
                webcanvas.itemconfigure(item_id,state='normal')
    item=canvas.create_image(side//2,side//2,image=frames[0][0])
    root.update();hwnd=root.winfo_id();style=user32.GetWindowLongW(hwnd,-20)
    user32.SetWindowLongW(hwnd,-20,style|0x20|0x80)
    silk.update_idletasks()
    whwnd=silk.winfo_id()
    wstyle=user32.GetWindowLongW(whwnd,-20)
    user32.SetWindowLongW(whwnd,-20,wstyle|0x20|0x80)
    cord.update_idletasks()
    chwnd=cord.winfo_id()
    cstyle=user32.GetWindowLongW(chwnd,-20)
    user32.SetWindowLongW(chwnd,-20,cstyle|0x20|0x80)

    now=time.monotonic();last=now
    state='rest';until=now+1.0
    nest_trace_enabled=os.environ.get('SPIDER_NEST_TRACE')=='1'
    gait=0.;travel_speed=0.;target_x=x;target_y=y
    cooldown=now+3.;leap_start=0.;leap_end=0.;leap_from=(x,y);leap_to=(x,y)
    previous_mouse=root.winfo_pointerxy();mouse_smooth=0.;last_interest=now
    # A motionless pointer is not an endlessly renewed disturbance. Previously
    # the spider would NEVER build a shelter if the pointer happened to be
    # nearby, because last_interest was reset on every 20-ms tick.
    last_mouse_moved=now
    alert_until=0.;alert_point=(x,y);alert_cooldown=0.;tap_start=0.;tap_end=0.;tap_origin=(x,y);tap_target=(x,y);tap_count=0;contact_until=0.;defend_until=0.;den_center=(x,y);den_guard_out=(x,y)
    # Idle silk-retreat state: after ~18s with no nearby cursor interest,
    # approach a screen edge, spin a small silk shelter, and rest there.
    retreat_target=(x,y);retreat_start=0.;silk_progress=0.
    next_retreat_allowed=now
    den_depart_goal=(x,y)
    # Local-only multi-instance positions. Each instance has a random ID.
    social=PeerRegistry() if os.environ.get('SPIDER_FIGHTS','1')!='0' else None
    near_peers=[]
    fight_peer_id=''
    fight_start=0.
    fight_anchor=(x,y)
    fight_cooldown=0.
    fight_contact_flash=0.
    fight_opponent=None
    fight_winner_role=0
    flee_target=(x,y)
    flee_from=(x,y)
    flee_until=0.
    victory_until=0.
    duel_fight_started=0.
    # New spontaneous natural actions are short and are never allowed to
    # interrupt hanging, nest weaving or an active contest.
    next_idle_action=now+random.uniform(7.,12.)
    idle_interval=max(2.,float(os.environ.get('SPIDER_IDLE_ACTION_SEC','9')))
    probe_started=0.;look_started=0.;look_heading=heading;look_duration=0.
    startle_cooldown=now+4.
    startle_chance=clamp(float(os.environ.get('SPIDER_STARTLE_CHANCE','.72')),0.,1.)
    startle_begin=(x,y);startle_end=(x,y);startle_started=0.;startle_duration=.48
    threat_seconds=max(2.0,float(os.environ.get('SPIDER_THREAT_SECONDS','3.15')))
    threat_started=0.
    # Find the visible rectangles of ordinary Windows app windows. Paths are
    # kept in screen coordinates; we never modify, focus or drag actual windows.
    edges_enabled=(os.environ.get('SPIDER_WINDOW_EDGES','1')!='0')
    edge_route=[]
    edge_index=0
    next_edge_try=now+random.uniform(5.,8.)
    edge_patrol_until=0.
    def leave_den(now):
        nonlocal den_depart_goal,target_x,target_y,next_retreat_allowed,last_interest
        # Forage outside the 72+ px den vicinity for 55–85 seconds, then
        # return to the same web naturally after a later idle period.
        den_depart_goal=departure_waypoint(den_center,sw,sh,side/2,
                                           home.vicinity_radius,
                                           jitter=random.uniform(-.48,.48),
                                           excursion=random.uniform(210.,330.))
        target_x,target_y=den_depart_goal
        last_interest=now
        next_retreat_allowed=now+random.uniform(forage_cooldown_min,forage_cooldown_max)
        travel_distance=math.hypot(target_x-x,target_y-y)
        transition('den_depart',max(8.,travel_distance/37.+3.))
    def choose_retreat():
        nonlocal retreat_target,web_corner,web_visible,silk_progress,den_center,nest_span,nest_calm_since,nest_render_stamp
        # Reuse the previous shelter, including one that has started fading,
        # instead of silently creating a new web at every idle period.
        if home.exists:
            retreat_target=home.position
            den_center=home.position
            web_corner=home.position
            return
        margin=side/2+12
        corners=[(margin,margin),(sw-margin,margin),(margin,sh-margin),(sw-margin,sh-margin)]
        retreat_target=min(corners,key=lambda pt:math.hypot(x-pt[0],y-pt[1]))
        web_corner=retreat_target
        den_center=retreat_target
        silk_progress=0.
        nest_span=INITIAL_SPAN
        nest_calm_since=0.
        nest_render_stamp=0.
        home.plan(retreat_target)
        silk_geometry(*web_corner)
        silk.withdraw()
        web_visible=False
    # Behavioral parameters are stylized, not literal biological measurements.
    def transition(name,duration):
        nonlocal state,until
        if nest_trace_enabled and name!=state:
            try:
                LOG.parent.mkdir(parents=True,exist_ok=True)
                with (LOG.parent/'nest_trace.txt').open('a',encoding='utf-8') as f:
                    f.write(f'{time.monotonic():.2f} {state} -> {name} at ({x:.1f},{y:.1f}); home={home.status}\n')
            except Exception:
                pass
        state=name;until=time.monotonic()+duration
    def choose_roam():
        nonlocal target_x,target_y
        r=random.uniform(size*1.5,size*4.0);a=random.uniform(-PI,PI)
        target_x=clamp(x+math.cos(a)*r,side/2,sw-side/2)
        target_y=clamp(y+math.sin(a)*r,side/2,sh-side/2)
    def start_tap(t,mx,my):
        nonlocal tap_start,tap_end,tap_origin,tap_target,tap_count
        tap_start=t;tap_end=t+random.uniform(.19,.27)
        tap_origin=(x,y)
        d=math.hypot(mx-x,my-y)
        # Short foreleg probing without moving the whole body over the cursor.
        reach=min(size*.16,max(0.,d-size*.42))
        tap_target=(clamp(x+(mx-x)/max(1,d)*reach,side/2,sw-side/2),
                    clamp(y+(my-y)/max(1,d)*reach,side/2,sh-side/2))
        tap_count+=1
        transition('tap',tap_end-t)
    def start_fight(now,peer):
        nonlocal fight_peer_id,fight_start,fight_anchor,fight_contact_flash,last_interest,travel_speed
        nonlocal next_retreat_allowed,fight_opponent,fight_winner_role,threat_started
        fight_peer_id=peer['id']
        # The lexicographically smaller ID owns the duel clock. The second
        # process adopts that clock on receiving the first one's heartbeat.
        if peer.get('fight_with')==social.id and str(peer['id'])<social.id and peer.get('fight_start'):
            fight_start=float(peer['fight_start'])
        else:
            fight_start=time.time()+threat_seconds+.30
        fight_anchor=(x,y)
        fight_opponent=peer
        threat_started=now
        fight_winner_role=winner_role(social.id,peer['id'])
        fight_contact_flash=0.
        last_interest=now
        next_retreat_allowed=max(next_retreat_allowed,now+65.)
        travel_speed=0.
        transition('threat_display',threat_seconds+.8)

    def break_retreat(now,mouse):
        nonlocal ruin_start,web_visible,silk_progress,next_retreat_allowed,last_interest
        nonlocal anger_until,anger_strikes,anger_next_strike,anger_point,anger_backoff
        nonlocal target_x,target_y,travel_speed,alert_cooldown,den_depart_goal,nest_calm_since
        nonlocal hang_drop_start,hang_drop_end,hang_drop_begin,hang_drop_dx,hang_drop_height
        was_hanging=state in ('hang_descend','hang_dwell','hang_ascend')
        if not home.completed or not web_visible:
            return
        previous_den=home.position
        home.clear()             # no abandoned den remains for choose_retreat() to reuse
        disruption.trigger(now, random.uniform(100.,140.))
        next_retreat_allowed=max(next_retreat_allowed,disruption.rebuild_after)
        last_interest=now
        ruin_start=now
        silk_progress=0.
        nest_calm_since=0.
        # Clear inherited destinations so no retreat-return state can take over.
        target_x,target_y=mouse
        den_depart_goal=(x,y)
        travel_speed=0.
        anger_point=mouse
        anger_until=now+random.uniform(anger_duration_min,anger_duration_max)
        anger_strikes=0
        anger_next_strike=now+.22
        alert_cooldown=now+2.
        # A broken overhead anchor makes a suspended spider fall briefly.
        # Then it recovers and starts the already existing defensive routine.
        hide_cord()
        if was_hanging:
            hang_drop_start=now
            hang_drop_end=now+.54
            hang_drop_begin=(x,y)
            hang_drop_dx=random.uniform(-size*.10,size*.10)
            hang_drop_height=min(size*.80,45.,max(0.,sh-side/2-y))
            transition('hang_drop',hang_drop_end-now)
        else:
            transition('rage_scan',.30)

    def start_hang_prepare(now):
        nonlocal hang_anchor,travel_speed
        # Walk from the resting corner toward a real visible strand attachment
        # on the outer diagonal, THEN descend into open desktop space.
        hang_anchor=calculate_hanging_anchor(nest_corner,nest_span,sw,sh,websize)
        travel_speed=0.
        distance=math.hypot(x-hang_anchor[0],y-hang_anchor[1])
        transition('hang_prepare',max(4.,distance/48.+2.))

    def start_hanging(now):
        nonlocal hang_started,hang_begin,hang_end,hang_anchor,hang_next_allowed,hang_top
        nonlocal heading,travel_speed,hang_rest_started,x,y
        # Place the body CLEARLY below the web edge before descending.
        # The earlier offset kept the body visually inside the corner silk,
        # so users mainly saw the thread moving instead of the spider itself.
        top_y=max(hang_anchor[1]+size*.72, side/2+size*.10)
        x=hang_anchor[0]
        y=top_y
        hang_started=now
        hang_top=(hang_anchor[0],top_y)
        hang_begin=hang_top
        # Keep the body nearly under the anchor, but descend deep enough to be
        # unmistakably visible in open desktop space.
        hang_end=(hang_anchor[0]+random.uniform(-size*.05,size*.05),
                  hanging_depth(top_y,sh,side/2,size)+size*.10)
        hang_next_allowed=now+random.uniform(hang_repeat_min,hang_repeat_max)
        hang_rest_started=0.
        heading=PI/2
        travel_speed=0.
        transition('hang_descend',hang_descend_seconds)

    def update_hanging_cord(photo):
        nonlocal cord_shown
        hanging = state in ('hang_descend','hang_dwell','hang_ascend') and home.completed
        if not hanging:
            hide_cord()
            return
        # Both silk and BODY are rendered in cordcanvas. The body is drawn
        # after the silk so that the fibre emerges from behind the abdomen.
        ax,ay=hang_anchor
        # The rope ends behind the spider's upper abdomen. The spider image
        # extends farther below; include its WHOLE bounding square in overlay.
        body_attach_y=y-size*.29
        left=round(clamp(ax-cord_width/2,0,max(0,sw-cord_width)))
        top=round(clamp(ay,0,sh-1))
        body_local_x=x-left
        body_local_y=y-top
        rope_local_x=ax-left
        rope_local_top=ay-top
        rope_local_bottom=max(rope_local_top+2.,body_attach_y-top)
        needed_height=max(12,round(body_local_y+size*.65),round(rope_local_bottom+3.))
        height=min(max(12,needed_height),max(12,sh-top))
        cordcanvas.configure(width=cord_width,height=height)
        cord.geometry(f'{cord_width}x{height}+{left}+{top}')
        cordcanvas.delete('all')
        cordcanvas.create_line(rope_local_x,rope_local_top,
                               body_local_x,rope_local_bottom,
                               fill='#66636d',width=2)
        cordcanvas.create_line(rope_local_x,rope_local_top,
                               body_local_x,rope_local_bottom,
                               fill='#e5e2eb',width=1)
        cordcanvas.create_image(body_local_x,body_local_y,image=photo,anchor='center')
        # Hide the original spider so that a stationary duplicate never remains
        # at the top of the web while the sprite on the thread descends.
        canvas.itemconfigure(item,state='hidden')
        if not cord_shown:
            cord.deiconify()
            cord_shown=True
        try:cord.lift(root)
        except tk.TclError:pass

    def start_rage_leap(now,mx,my):
        nonlocal leap_from,leap_to,leap_start,leap_end,cooldown
        nonlocal anger_strikes,anger_next_strike,anger_point
        dx,dy=mx-x,my-y
        d=math.hypot(dx,dy)
        # Keep cursor at foreleg reach, as in v20, never beneath the abdomen.
        distance=min(size*5.3,max(0.,d-size*.65))
        if distance<10.:
            # If the pointer is almost touching the body, retreat to create
            # realistic foreleg clearance rather than jumping in place.
            nonlocal anger_backoff,anger_rear_from,anger_rear_start,anger_rear_end
            away=math.atan2(y-my,x-mx) if d>2 else heading+PI
            anger_backoff=(clamp(x+math.cos(away)*size*1.05,side/2,sw-side/2),
                           clamp(y+math.sin(away)*size*1.05,side/2,sh-side/2))
            anger_rear_from=(x,y)
            anger_rear_start=now
            anger_rear_end=now+.28
            transition('rage_rear',.28)
            return
        a=math.atan2(dy,dx)
        leap_from=(x,y)
        leap_to=(clamp(x+math.cos(a)*distance,side/2,sw-side/2),
                 clamp(y+math.sin(a)*distance,side/2,sh-side/2))
        leap_start=now
        leap_end=now+clamp(distance/900.,.18,.34)
        cooldown=now+1.0
        anger_strikes+=1
        anger_next_strike=now+random.uniform(1.0,1.8)
        anger_point=(mx,my)
        transition('rage_leap',leap_end-now)

    def tick():
        nonlocal x,y,heading,last,gait,travel_speed,target_x,target_y,cooldown
        nonlocal leap_start,leap_end,leap_from,leap_to,previous_mouse,mouse_smooth,last_interest,last_mouse_moved
        nonlocal alert_until,alert_point,alert_cooldown,tap_start,tap_end,tap_origin,tap_target,tap_count,contact_until,defend_until,den_center,den_guard_out
        nonlocal retreat_start,silk_progress,web_visible,shown_fade_step,web_corner,next_retreat_allowed
        nonlocal ruin_start,anger_until,anger_strikes,anger_next_strike,anger_point
        nonlocal anger_backoff,anger_rear_start,anger_rear_from,anger_rear_end
        nonlocal fight_peer_id,fight_start,fight_anchor,fight_cooldown,fight_opponent
        nonlocal fight_contact_flash,near_peers,edge_route,edge_index,next_edge_try,edge_patrol_until
        nonlocal fight_winner_role,flee_target,flee_from,flee_until,victory_until
        nonlocal next_idle_action,probe_started,look_started,look_heading,look_duration
        nonlocal startle_cooldown,startle_begin,startle_end,startle_started,startle_duration,threat_started
        nonlocal nest_span,nest_calm_since,nest_ready_at,nest_render_stamp,nest_render_span
        nonlocal hang_next_allowed,hang_started,hang_begin,hang_end,hang_anchor,hang_top
        nonlocal hang_drop_start,hang_drop_end,hang_drop_begin,hang_drop_dx,hang_drop_height,hang_rest_started,hang_trace_at
        now=time.monotonic();dt=clamp(now-last,0.001,.05);last=now
        if all(user32.GetAsyncKeyState(k)&0x8000 for k in (0x11,0x10,0x51)):
            root.destroy();return
        mx,my=root.winfo_pointerxy()
        if social is not None:
            near_peers=social.scan()
            # Keep the other program's visible position (not merely two sprites
            # running a prerecorded fight sequence) for facing and contact.
            if state in ('threat_display','fight'):
                fight_opponent=next((v for v in near_peers if v['id']==fight_peer_id),None)
                if fight_opponent and (fight_opponent.get('fight_with')==social.id
                                       and str(fight_opponent['id'])<social.id
                                       and fight_opponent.get('fight_start')):
                    fight_start=float(fight_opponent['fight_start'])
            elif now>fight_cooldown and not state.startswith('rage_') and state not in ('weave','leap','rage_rear','fight_flee','fight_victory','hang_prepare','hang_descend','hang_dwell','hang_ascend','hang_drop'):
                candidates=sorted(near_peers,key=lambda a:math.hypot(a['x']-x,a['y']-y))
                if candidates:
                    enemy=candidates[0]
                    dd=math.hypot(enemy['x']-x,enemy['y']-y)
                    # Increased reaction distance when another spider is already
                    # offering a challenge. No fight with stale registry entries.
                    limit=max(size*3.2,165.)
                    if enemy.get('fight_with')==social.id:limit*=1.35
                    if dd<limit:
                        start_fight(now,enemy)
        # The entire triangular web (including expanded outer strands) is
        # clickable via screen-wide pointer coordinates. This works even while
        # the spider is away, so a large shelter can always be destroyed.
        if (home.completed and web_visible and not ruin_start
                and now>nest_ready_at+.85
                # A growing web must not break merely because it expands under
                # a pointer that was already resting in that part of the screen.
                and (mx,my)!=previous_mouse
                and point_in_triangle((mx,my),triangle_screen(nest_corner,nest_span,sw,sh,websize))):
            break_retreat(now,(mx,my))
        # Torn silk falls away even after the den is gone from the behavioural model.
        if ruin_start:
            broken_p=clamp((now-ruin_start)/ruin_seconds,0.,1.)
            if broken_p<1.:
                draw_broken_silk(broken_p)
            else:
                silk.withdraw()
                webcanvas.delete('all')
                web_visible=False
                web_corner=None
                ruin_start=0.
                nest_span=INITIAL_SPAN
        pointer_step=math.hypot(mx-previous_mouse[0],my-previous_mouse[1])
        pointer_moved=pointer_step>=1.5
        if pointer_moved:
            last_mouse_moved=now
        pointer_active=(now-last_mouse_moved)<.55
        raw_mouse_speed=pointer_step/dt
        # Detect fast crossing of a nearby region, even if the cursor ends far away.
        px,py=previous_mouse
        vx=mx-px;vy=my-py;v2=vx*vx+vy*vy
        t=clamp(((x-px)*vx+(y-py)*vy)/v2,0.,1.) if v2>1 else 0.
        closest=math.hypot(px+t*vx-x,py+t*vy-y)
        if (v2>1 and math.sqrt(v2)/dt>450 and closest<size*3.3
                and now>alert_cooldown and state not in ('leap','crouch','tap','recover','hang_prepare','hang_descend','hang_dwell','hang_ascend','hang_drop','flinch','backstep')
                and not state.startswith('rage_') and state not in ('threat_display','fight','fight_flee','fight_victory')):
            alert_point=(mx,my) if math.hypot(mx-x,my-y)>5 else (px,py)
            alert_until=now+random.uniform(.40,.70)
            alert_cooldown=now+1.15
            travel_speed=0.
            if now>=startle_cooldown and raw_mouse_speed>800 and random.random()<startle_chance:
                startle_begin=(x,y)
                startle_end=retreat_backstep((x,y),alert_point,size,(sw,sh))
                startle_cooldown=now+random.uniform(8.,15.)
                transition('flinch',.13)
            else:
                transition('alert',alert_until-now)
        previous_mouse=(mx,my)
        mouse_smooth+=clamp(dt*5,0,1)*(raw_mouse_speed-mouse_smooth)
        dmouse=math.hypot(mx-x,my-y)
        visible=dmouse<max(270,size*5.2)
        # Cursor is a visual stimulus, not always an automatic target.
        # Very fast cursor movements trigger observation rather than an impossible chase.
        calm_target=visible and mouse_smooth<750 and dmouse>size*.52
        if visible and pointer_active and state not in ('fight','fight_flee','fight_victory'):
            if pointer_moved:
                last_interest=now
            if state in ('retreat_walk','weave'):
                transition('alert',random.uniform(.25,.45))
            elif state=='den_depart' and dmouse<size*2.5:
                # An outing remains interruptible by a nearby moving stimulus.
                transition('alert',random.uniform(.25,.45))
            elif state in ('edge_seek','edge_patrol') and dmouse<max(170.,size*3.5):
                edge_route=[]
                next_edge_try=now+12.
                transition('alert',random.uniform(.18,.36))
        elif (not state.startswith('rage_') and disruption.can_rebuild(now)
              and retreat_is_due(now,last_interest,idle_after,next_retreat_allowed)
              and state not in ('retreat_walk','weave','retreat_rest','den_depart',
                                'defend_emerge','defend_hold','retreat_return',
                                'leap','crouch','tap','contact','tap_prepare','fight',
                                'edge_seek','edge_patrol','fight_flee','fight_victory',
                                'hang_prepare','hang_descend','hang_dwell','hang_ascend','hang_drop',
                                'probe','look_around','flinch','backstep','threat_display')):
            choose_retreat();transition('retreat_walk',12.)
            last_interest=now
        if state=='threat_display':
            if (fight_opponent is None or fight_opponent.get('fight_with')!=social.id) and now-threat_started>1.5:
                # Peer vanished / duel cancelled: do not attack empty screen.
                fight_peer_id='';fight_opponent=None
                fight_cooldown=now+15.
                transition('rest',random.uniform(.4,.8))
            elif time.time()>=fight_start:
                transition('fight',DUEL_DURATION+.5)
        elif state=='probe':
            if now>=until:transition('rest',random.uniform(.4,.85))
        elif state=='look_around':
            if now>=until:
                heading=look_heading
                transition('rest',random.uniform(.4,.85))
        elif state=='flinch':
            if now>=until:
                startle_started=now
                startle_duration=random.uniform(.37,.52)
                transition('backstep',startle_duration)
        elif state=='backstep':
            if now>=until:
                transition('observe' if math.hypot(mx-x,my-y)<size*3. else 'rest',random.uniform(.3,.7))
        elif state=='hang_prepare':
            distance=math.hypot(x-hang_anchor[0],y-hang_anchor[1])
            if distance<9.:
                start_hanging(now)
            elif now>=until:
                # Keep walking to the anchor: never teleport across the web.
                transition('hang_prepare',max(3.,distance/45.+1.))
        elif state=='hang_descend':
            if now>=until:
                hang_rest_started=now
                transition('hang_dwell',random.uniform(hang_dwell_min,hang_dwell_max))
        elif state=='hang_dwell':
            if now>=until:
                hang_started=now
                hang_begin=(x,y)
                hang_end=hang_top
                transition('hang_ascend',hang_ascend_seconds)
        elif state=='hang_ascend':
            if now>=until:
                hide_cord()
                if home.completed:
                    home.returned(now)
                    transition('retreat_return',.65)
                else:
                    transition('rest',.4)
        elif state=='hang_drop':
            if now>=hang_drop_end:
                transition('rage_scan',.30)
        elif state=='fight':
            elapsed=time.time()-fight_start
            opp=fight_opponent
            role=int(social.id>fight_peer_id)
            winner=fight_winner_role
            lost=(role!=winner)
            if not opp or elapsed>=DUEL_DURATION or math.hypot(opp['x']-x,opp['y']-y)>max(650.,size*12.):
                enemy=(opp['x'],opp['y']) if opp else (fight_anchor[0]-size,fight_anchor[1])
                fight_peer_id=''
                fight_opponent=None
                fight_cooldown=now+random.uniform(48.,65.)
                next_retreat_allowed=max(next_retreat_allowed,now+55.)
                if lost:
                    flee_from=(x,y)
                    flee_target=escape_destination((x,y),enemy,(sw,sh),side/2,
                                                     distance=max(430.,size*9.))
                    flee_until=now+6.3
                    target_x,target_y=flee_target
                    transition('fight_flee',6.3)
                else:
                    victory_until=now+random.uniform(.7,1.35)
                    transition('fight_victory',victory_until-now)
        elif state=='fight_flee':
            if now>=flee_until or (math.hypot(x-flee_target[0],y-flee_target[1])<10
                                    and now>flee_until-2.0):
                # The loser doesn't simply walk alongside the victor again.
                choose_roam()
                next_retreat_allowed=max(next_retreat_allowed,now+25.)
                transition('explore',random.uniform(.6,1.2))
        elif state=='fight_victory':
            if now>=victory_until:
                choose_roam()
                transition('explore',random.uniform(.55,1.1))
        elif state=='edge_seek':
            if not edge_route:
                transition('rest',.25)
            elif math.hypot(x-edge_route[0][0],y-edge_route[0][1])<9:
                edge_index=1
                edge_patrol_until=now+random.uniform(8.,13.)
                transition('edge_patrol',edge_patrol_until-now)
            elif now>=until:
                transition('rest',random.uniform(.3,.8))
        elif state=='edge_patrol':
            if not edge_route or now>=edge_patrol_until or edge_index>=len(edge_route):
                edge_route=[]
                next_edge_try=now+random.uniform(16.,25.)
                transition('rest',random.uniform(.6,1.2))
            elif math.hypot(x-edge_route[edge_index][0],y-edge_route[edge_index][1])<10:
                edge_index+=1
        elif state=='rage_scan':
            # The spider freezes, turns rapidly and fixes on the disturbance.
            if now>=until:
                transition('rage_pursue',random.uniform(1.3,2.3))
        elif state=='rage_pursue':
            # Threat response ranges further than everyday curious stalking.
            if now>=anger_until:
                transition('rage_finish',.28)
            elif anger_strikes>=anger_max_strikes:
                # Keep an alert/territorial display to the end of the timer
                # instead of unexpectedly ending right after the final lunge.
                if now>=until:transition('rage_scan',random.uniform(.25,.48))
            elif math.hypot(mx-x,my-y)<max(500.,size*8.5):
                anger_point=(mx,my)
                dist=math.hypot(mx-x,my-y)
                aligned=abs(angle_diff(math.atan2(my-y,mx-x),heading))<.50
                if (anger_strikes<anger_max_strikes and dist<size*.69 and now>anger_next_strike):
                    # Cursor overlaps body: recoil a step to make room to lunge.
                    away=math.atan2(y-my,x-mx) if dist>2 else heading+PI
                    anger_backoff=(clamp(x+math.cos(away)*size*1.15,side/2,sw-side/2),
                                   clamp(y+math.sin(away)*size*1.15,side/2,sh-side/2))
                    anger_rear_from=(x,y);anger_rear_start=now;anger_rear_end=now+.26
                    transition('rage_rear',.26)
                elif (anger_strikes<anger_max_strikes and dist<max(size*4.5,215.)
                      and aligned and now>anger_next_strike):
                    start_rage_leap(now,mx,my)
                elif now>=until:
                    transition('rage_scan',random.uniform(.12,.25))
            elif now>=until:
                # Don't chase a mouse across the entire desktop forever.
                transition('rage_scan',random.uniform(.12,.25))
        elif state=='rage_rear':
            if now>=until:
                if now<anger_until:
                    transition('rage_pursue',.55)
                else:
                    transition('rage_finish',.28)
        elif state=='rage_leap':
            if now>=leap_end:
                transition('rage_recover',random.uniform(.22,.40))
        elif state=='rage_recover':
            if now>=until:
                if now<anger_until:
                    transition('rage_pursue',random.uniform(.9,1.6))
                else:
                    transition('rage_finish',.28)
        elif state=='rage_finish':
            if now>=until:
                # Free roaming: no destroyed shelter to return to.
                choose_roam()
                transition('explore',random.uniform(.7,1.1))
        elif state=='retreat_walk':
            if math.hypot(x-retreat_target[0],y-retreat_target[1])<8:
                # A completed shelter is reused. No new weaving cycle is started.
                if home.exists and home.completed:
                    home.returned(now)
                    draw_silk(1.)
                    set_silk_opacity(1.)
                    silk.deiconify();web_visible=True
                    transition('retreat_rest',den_rest_duration())
                else:
                    if not home.exists:
                        choose_retreat()
                    home.start_build()
                    retreat_start=now-silk_progress*5.5
                    silk_geometry(*retreat_target)
                    silk.deiconify();web_visible=True
                    transition('weave',5.5*(1.-silk_progress))
            elif now>=until:
                # Large monitors may require more than 12 seconds to reach a corner.
                # Continue walking: never build remotely or reset the expiry clock.
                transition('retreat_walk',12.)
        elif state=='weave':
            silk_progress=clamp((now-retreat_start)/5.5,0.,1.)
            draw_silk(silk_progress)
            if silk_progress>=1. or now>=until:
                silk_progress=1.
                draw_silk(1.)
                home.finish(now)
                nest_ready_at=now
                nest_calm_since=now
                transition('retreat_rest',den_rest_duration())
        elif state=='retreat_rest':
            # Only a mature top-corner web may support a hanging excursion.
            if (now>=hang_next_allowed and not pointer_active and
                    can_begin_hanging(nest_corner,nest_span,
                                      max_web_span(sw,sh),home.completed,hang_min_web_ratio)):
                start_hang_prepare(now)
            elif visible and pointer_active and dmouse < max(size*3.2, 110):
                # Only an active approach elicits defensive posture; a still
                # pointer next to the shelter must not pin the spider forever.
                ang=math.atan2(my-den_center[1], mx-den_center[0])
                den_guard_out=(clamp(den_center[0]+math.cos(ang)*max(size*0.8,14), side/2, sw-side/2),
                               clamp(den_center[1]+math.sin(ang)*max(size*0.8,14), side/2, sh-side/2))
                defend_until=now+random.uniform(1.0,1.6)
                transition('defend_emerge', defend_until-now)
            elif now>=until:
                # This is the previously missing autonomous den exit.
                leave_den(now)
        elif state=='den_depart':
            # Keep walking to a deliberate waypoint away from the silk shelter.
            if math.hypot(x-den_depart_goal[0],y-den_depart_goal[1])<11 or now>=until:
                transition('rest',random.uniform(.5,1.2))
        elif state=='defend_emerge':
            if now>=until:
                if visible:
                    if now>cooldown and dmouse < max(size*2.2,72):
                        transition('tap_prepare', .14)
                    else:
                        transition('defend_hold', random.uniform(.45,.95))
                else:
                    transition('retreat_return', .55)
        elif state=='defend_hold':
            if not visible or dmouse > max(size*4.3, 145):
                transition('retreat_return', .55)
            elif now>=until:
                if now>cooldown and dmouse < max(size*2.1,70):
                    transition('tap_prepare', .14)
                else:
                    transition('defend_hold', random.uniform(.35,.85))
        elif state=='retreat_return':
            if math.hypot(x-den_center[0], y-den_center[1])<7:
                transition('retreat_rest',den_rest_duration())
            elif now>=until:
                # Returning can take longer than 0.55 s; don't freeze mid-route.
                transition('retreat_return',1.0)
        elif state=='alert':
            if now>=until:transition('observe',random.uniform(.22,.42))
        elif state=='tap':
            if now>=tap_end:
                contact_until=now+random.uniform(.22,.43)
                transition('contact',contact_until-now)
        elif state=='contact':
            if now>=until:
                if web_visible and home.completed and math.hypot(x-den_center[0], y-den_center[1]) < max(size*1.8,50) and visible:
                    if visible and dmouse<size*.95 and tap_count<2 and random.random()<.55:
                        transition('tap_prepare',.16)
                    else:
                        transition('defend_hold', random.uniform(.35,.8))
                elif visible and dmouse<size*.90 and tap_count<2 and random.random()<.55:
                    transition('tap_prepare',.16)
                else:transition('recover',random.uniform(.45,.8))
        elif state=='tap_prepare':
            if now>=until: start_tap(now,mx,my)
        elif state=='rest':
            if now>=until and now>=next_idle_action and not visible and not pointer_active:
                next_idle_action=now+random.uniform(idle_interval*.70,idle_interval*1.50)
                if random.random()<.55:
                    probe_started=now
                    transition('probe',random.uniform(.9,1.55))
                else:
                    look_heading=heading;look_started=now
                    look_duration=random.uniform(1.5,2.4)
                    transition('look_around',look_duration)
            # Optional window-frame walk during free exploration. The normal
            # cursor reaction always takes priority.
            if state=='rest' and edges_enabled and now>=next_edge_try and not calm_target and not visible and now>=until:
                next_edge_try=now+random.uniform(20.,30.)
                windows=visible_windows(screen_size=(sw,sh))
                chosen=choose_nearby_window(windows,x,y,max(side/2,70),limit=max(400.,size*8.))
                if chosen:
                    _,_,rect=chosen
                    margin=side/2+8
                    a,b,c,d=rect
                    r=(max(a,margin),max(b,margin),min(c,sw-margin),min(d,sh-margin))
                    if r[2]-r[0]>100 and r[3]-r[1]>75:
                        edge_route=patrol_route(r,x,y,clockwise=bool(random.getrandbits(1)))
                        edge_index=0
                        transition('edge_seek',max(5.,math.hypot(edge_route[0][0]-x,edge_route[0][1]-y)/48.+3.))
            if state=='rest' and calm_target and now>=until:
                transition('orient',random.uniform(.20,.48))
            elif state=='rest' and now>=until:
                if random.random()<.70:
                    choose_roam();transition('explore',random.uniform(.35,.85))
                else:transition('rest',random.uniform(.65,1.6))
        elif state=='explore':
            if calm_target and now>=until-.18:transition('orient',random.uniform(.18,.38))
            elif now>=until or math.hypot(target_x-x,target_y-y)<8:
                transition('rest',random.uniform(.35,1.0))
        elif state=='orient':
            if now>=until:
                if calm_target and dmouse>size*1.35:
                    transition('stalk',random.uniform(.23,.58))
                else:transition('observe',random.uniform(.4,1.0))
        elif state=='stalk':
            if not calm_target:transition('observe',random.uniform(.35,.8))
            elif now>=until:
                # Stop-and-go stalk: hold still to reassess before advancing.
                transition('observe',random.uniform(.25,.62))
        elif state=='observe':
            if now>=until:
                aligned=abs(angle_diff(math.atan2(my-y,mx-x),heading))<.26
                # Short deliberate leap only when close and aligned, with a cooldown.
                if calm_target and size*.75<dmouse<size*4.2 and aligned and now>cooldown and mouse_smooth<450:
                    transition('crouch',random.uniform(.14,.24))
                elif visible and dmouse<=size*.88:
                    if now>cooldown:transition('tap_prepare',.15)
                    else:transition('rest',random.uniform(.30,.6))
                elif calm_target and dmouse>size*.78:
                    transition('orient',random.uniform(.12,.3))
                else:transition('rest',random.uniform(.4,1.1))
        elif state=='crouch':
            if now>=until:
                if calm_target and abs(angle_diff(math.atan2(my-y,mx-x),heading))<.42:
                    leap_from=(x,y)
                    # Land with the cursor just ahead of the forelegs, not underneath the abdomen.
                    jump_distance=min(size*4.5,max(0.,dmouse-size*.58))
                    leap_to=(clamp(x+math.cos(heading)*jump_distance,side/2,sw-side/2),
                             clamp(y+math.sin(heading)*jump_distance,side/2,sh-side/2))
                    leap_start=now;leap_end=now+random.uniform(.18,.25)
                    cooldown=now+random.uniform(2.8,4.6)
                    tap_count=0
                    transition('leap',leap_end-now)
                else:transition('observe',.45)
        elif state=='leap':
            if now>=leap_end:
                if math.hypot(mx-x,my-y)<size*.95:
                    transition('tap_prepare',.11)
                else:transition('recover',random.uniform(.22,.45))
        elif state=='recover':
            if now>=until:transition('rest',random.uniform(.5,1.3))

        prev_x,prev_y=x,y;turn=0.
        if state in ('hang_descend','hang_dwell','hang_ascend'):
            # The body is suspended beneath a fixed anchor, so only slow sway
            # is added. Legs must not keep running while no steps are made.
            hang_time=now-hang_started
            if state=='hang_descend':
                p=clamp(hang_time/hang_descend_seconds,0.,1.)
                x,y=hanging_position(hang_begin,hang_end,p,
                                      sway=math.sin(hang_time*2.4)*size*.020)
            elif state=='hang_dwell':
                x=hang_end[0]+math.sin(hang_time*1.5)*size*.040
                y=hang_end[1]+math.sin(hang_time*.90)*size*.018
            else:
                p=clamp(hang_time/hang_ascend_seconds,0.,1.)
                x,y=hanging_position(hang_begin,hang_end,p,
                                      sway=math.sin(hang_time*2.2)*size*.016)
            x=clamp(x,side/2,sw-side/2)
            y=clamp(y,side/2,sh-side/2)
            heading=PI/2
            travel_speed=0.
        elif state=='hang_drop':
            p=clamp((now-hang_drop_start)/max(.02,hang_drop_end-hang_drop_start),0.,1.)
            x,y=drop_position(hang_drop_begin,p,hang_drop_height,hang_drop_dx)
            x=clamp(x,side/2,sw-side/2)
            y=clamp(y,side/2,sh-side/2)
            heading=PI/2+math.sin(p*PI)*.35
            travel_speed=0.
        elif state=='threat_display' and fight_opponent:
            opponent=fight_opponent
            dx=opponent['x']-x;dy=opponent['y']-y
            if math.hypot(dx,dy)>2.:
                desired=math.atan2(dy,dx)
                heading=(heading+clamp(angle_diff(desired,heading),-10.*dt,10.*dt)+PI)%(2*PI)-PI
            left=max(.0,threat_seconds+.30-(fight_start-time.time()))
            p=clamp(left/threat_seconds,0.,1.)
            role=int(social.id>fight_peer_id)
            tx,ty=threat_display_motion(fight_anchor,(opponent['x'],opponent['y']),size,role,p)
            tx=clamp(tx,side/2,sw-side/2);ty=clamp(ty,side/2,sh-side/2)
            md=math.hypot(tx-x,ty-y)
            if md>.4:
                s=min(md,75.*dt)
                x+=s*(tx-x)/md;y+=s*(ty-y)/md
            travel_speed=0.
        elif state=='backstep':
            p=clamp((now-startle_started)/startle_duration,0.,1.)
            smooth=p*p*(3.-2.*p)
            x=startle_begin[0]+(startle_end[0]-startle_begin[0])*smooth
            y=startle_begin[1]+(startle_end[1]-startle_begin[1])*smooth
            dist_moved=math.hypot(x-prev_x,y-prev_y)
            if dist_moved>.1:
                gait=(gait-128.*dist_moved/gait_cycle_distance(size,90.))%128.
            travel_speed=0.
        elif state=='look_around':
            heading=observe_rotation(look_heading,now-look_started,look_duration)
            travel_speed=0.
        elif state=='fight' and fight_opponent:
            opponent=fight_opponent
            dx=opponent['x']-x;dy=opponent['y']-y
            dist=math.hypot(dx,dy)
            if dist>2:
                desired=math.atan2(dy,dx)
                heading=(heading+clamp(angle_diff(desired,heading),-16.*dt,16.*dt)+PI)%(2*PI)-PI
            role=int(social.id>fight_peer_id)
            stage,attacking,p=duel_phase(time.time()-fight_start,role,fight_winner_role)
            target=(x,y)
            fight_speed=0.
            if stage in ('strike','finisher'):
                # Hold the defender still until the attacking spider touches it.
                # A sharp impact, recoil and retraction then follow.
                target,fight_speed=strike_motion((x,y),fight_anchor,
                    (opponent['x'],opponent['y']),size,opponent['size'],
                    attacking,p,stage=='finisher')
                # Show the contact pose only when the sprites are actually close.
                touch=foot_contact_clearance(size,opponent['size'])
                if .42<p<.73 and dist<touch+size*.19:
                    fight_contact_flash=now+.10
            elif stage=='recover':
                target=fight_anchor
                fight_speed=270.
            tx=clamp(target[0],side/2,sw-side/2)
            ty=clamp(target[1],side/2,sh-side/2)
            md=math.hypot(tx-x,ty-y)
            if md>1.:
                delta=min(md,fight_speed*dt)
                x+=delta*(tx-x)/md
                y+=delta*(ty-y)/md
            walked=math.hypot(x-prev_x,y-prev_y)
            if walked>0.35:
                gait=(gait+128.*walked/gait_cycle_distance(size,fight_speed,combat=True))%128.
            travel_speed=fight_speed if md>3 else 0.
        elif state=='tap':
            p=clamp((now-tap_start)/max(.01,tap_end-tap_start),0.,1.)
            # Deliberate double action: extend to the pointer, briefly retract.
            k=math.sin(PI*p)**2
            x=tap_origin[0]+(tap_target[0]-tap_origin[0])*k
            y=tap_origin[1]+(tap_target[1]-tap_origin[1])*k
            travel_speed=0.
        elif state in ('leap','rage_leap'):
            p=clamp((now-leap_start)/max(.01,leap_end-leap_start),0,1)
            # smooth accelerated takeoff and decelerated landing
            smooth=p*p*(3-2*p)
            x=leap_from[0]+(leap_to[0]-leap_from[0])*smooth
            y=leap_from[1]+(leap_to[1]-leap_from[1])*smooth
            travel_speed=0.
        elif state=='rage_rear':
            p=clamp((now-anger_rear_start)/max(.01,anger_rear_end-anger_rear_start),0.,1.)
            smooth=p*p*(3.-2.*p)
            x=anger_rear_from[0]+(anger_backoff[0]-anger_rear_from[0])*smooth
            y=anger_rear_from[1]+(anger_backoff[1]-anger_rear_from[1])*smooth
            travel_speed=0.
        else:
            if state in ('rage_scan','rage_pursue'):
                # Follow the current cursor rather than its original den location.
                tx,ty=(mx,my) if math.hypot(mx-x,my-y)<max(510.,size*8.7) else anger_point
            elif state=='weave':
                # Small looping movement around the den while laying silk.
                p=clamp((now-retreat_start)/5.5,0.,1.)
                ang=2*PI*(1.2*p)
                rad=max(size*0.28, 7)
                tx=den_center[0]+math.cos(ang)*rad
                ty=den_center[1]+math.sin(ang*1.25)*rad*0.65
            elif state=='defend_emerge' or state=='defend_hold':
                tx,ty=den_guard_out
            elif state=='retreat_return':
                tx,ty=den_center
            elif state=='hang_prepare':
                tx,ty=hang_anchor
            elif state=='den_depart':
                tx,ty=den_depart_goal
            elif state=='fight_flee':
                tx,ty=flee_target
            elif state in ('edge_seek','edge_patrol') and edge_route:
                ix=0 if state=='edge_seek' else min(edge_index,len(edge_route)-1)
                tx,ty=edge_route[ix]
            elif state=='alert':
                tx,ty=alert_point
            elif state in ('orient','stalk','observe','crouch','tap_prepare','contact') and visible:
                tx,ty=mx,my
            elif state=='retreat_walk':tx,ty=retreat_target
            else:tx,ty=target_x,target_y
            dx=tx-x;dy=ty-y;dist=math.hypot(dx,dy)
            if state in ('orient','stalk','explore','observe','alert','tap_prepare','contact','retreat_walk','den_depart','defend_emerge','defend_hold','retreat_return','weave','hang_prepare','rage_scan','rage_pursue','edge_seek','edge_patrol','fight_flee') and dist>2:
                desired=math.atan2(dy,dx)
                rate=16. if state=='fight_flee' else (14. if state in ('alert','rage_scan','rage_pursue') else (5.5 if state=='orient' else 2.7))
                turn=clamp(angle_diff(desired,heading),-rate*dt,rate*dt)
                heading=(heading+turn+PI)%(2*PI)-PI
            alignment=max(0,math.cos(angle_diff(math.atan2(dy,dx),heading))) if dist>3 else 0
            # Discrete steps with slower leg cadence, never drifts while observing.
            wanted=0.
            if state=='fight_flee' and dist>8:wanted=clamp(dist*2.2,195.,270.)*alignment
            if state=='rage_pursue' and dist>size*.72:wanted=clamp(dist*1.5,90.,185.)*alignment
            if state in ('edge_seek','edge_patrol') and dist>5:wanted=clamp(dist*.9,32.,69.)*alignment
            if state=='stalk' and dist>size*.75:wanted=clamp(dist*.62,26.,62.)*alignment
            if state=='retreat_walk' and dist>8:wanted=62.*alignment
            if state=='den_depart' and dist>10:wanted=clamp(dist*.7,40.,72.)*alignment
            if state=='hang_prepare' and dist>9:wanted=clamp(dist*.8,38.,77.)*alignment
            if state=='weave' and dist>4:wanted=34.*alignment
            if state=='defend_emerge' and dist>2:wanted=54.*alignment
            if state=='defend_hold' and dist>2:wanted=18.*alignment
            if state=='retreat_return' and dist>2:wanted=48.*alignment
            if state=='explore' and dist>7:wanted=54.*alignment
            accel=(850. if wanted>travel_speed else 1100.) if state in ('rage_pursue','fight_flee') else (200. if wanted>travel_speed else 310.)
            travel_speed+=clamp(wanted-travel_speed,-accel*dt,accel*dt)
            safety_gap=size*.68 if state=='rage_pursue' else (size*.75 if state=='stalk' else 5)
            step=min(travel_speed*dt,max(0,dist-safety_gap))
            x+=math.cos(heading)*step;y+=math.sin(heading)*step
            x=clamp(x,side/2,sw-side/2);y=clamp(y,side/2,sh-side/2)
            # Synchronize leg cadence with actual body translation, including
            # normal walking and short sprints. No cycling while stationary.
            travel=math.hypot(x-prev_x,y-prev_y)
            if state in ('stalk','explore','retreat_walk','weave','defend_emerge','retreat_return','den_depart','hang_prepare','rage_pursue','edge_seek','edge_patrol','fight_flee'):
                gait=(gait+128.*travel/gait_cycle_distance(size,travel_speed,combat=state in ('rage_pursue','fight_flee')))%128.
            # Freeze feet during watch/crouch/recover, even if turning.
        # Grow the silk only during undisturbed idle time. Expansion adds
        # progressively more strands into a corner-to-corner triangular fan.
        if home.completed and web_visible and not ruin_start:
            if not nest_calm_since:
                nest_calm_since=now
            if visible and pointer_moved and dmouse < max(size*4.,230.):
                nest_calm_since=now
            next_span=grown_span(now-nest_calm_since,sw,sh,
                                delay=nest_growth_delay,expand_duration=nest_growth_seconds)
            if next_span>nest_span+.9:
                nest_span=next_span
                if now-nest_render_stamp>.20:
                    draw_silk(1.)
                    nest_render_stamp=now
                    if home.status=='fading':
                        set_silk_opacity(max(0.,1.-(now-(home.left_at or now)-home.abandon_after)/home.fade_seconds))
        # Compute abandonment from actual final body position. A completed den
        # stays intact while its owner remains nearby; return resets the clock.
        previous_status=home.status
        fade_opacity=home.update(now,(x,y))
        if previous_status=='fading' and home.status=='ready' and home.exists:
            # Returning during fade immediately restores the original silk.
            draw_silk(1.)
            set_silk_opacity(1.)
        elif home.status=='fading' and web_visible:
            set_silk_opacity(fade_opacity)
        elif previous_status in ('ready','fading') and not home.exists:
            # Five minutes abandoned + thirty seconds fading have elapsed.
            silk.withdraw()
            webcanvas.delete('all')
            web_visible=False
            web_corner=None
            silk_progress=0.
            nest_calm_since=0.
        direction=round(((90-math.degrees(heading))%360)/15)%24
        if state=='threat_display' and fight_opponent:
            phase=max(0.,threat_seconds+.30-(fight_start-time.time()))
            photo=threat[threat_frame(phase,threat_seconds)][direction]
        elif state=='probe':
            photo=frames[probe_frame(now-probe_started)][direction]
        elif state=='retreat_rest' and home.completed:
            # Tiny foreleg motion every several seconds without moving the nest.
            age=max(0.,now-nest_ready_at)
            slot=age%6.4
            photo=frames[probe_frame(slot-.7)][direction] if .7<slot<1.6 else frames[0][direction]
        elif state=='fight' and fight_opponent:
            fight_stage,attacking,_=duel_phase(time.time()-fight_start,int(social.id>fight_peer_id),fight_winner_role)
            if fight_stage=='display':
                photo=jumps[1][direction]  # raised front-body display
            elif fight_stage in ('strike','finisher') and time.monotonic()<fight_contact_flash:
                photo=jumps[2 if attacking else 1][direction]
            elif fight_stage in ('strike','finisher','recover'):
                photo=frames[int((gait+2)//4)%32][direction]
            else:
                photo=frames[2][direction]
        elif state in ('leap','rage_leap'):
            p=clamp((now-leap_start)/max(.01,leap_end-leap_start),0,1)
            height=math.sin(PI*p)
            jump_level=0 if height<.32 else (1 if height<.72 else 2)
            photo=jumps[jump_level][direction]
        elif state=='hang_drop':
            photo=jumps[1][direction]
        else:
            photo=frames[int((gait+2)//4)%32 if state in ('stalk','explore','retreat_walk','weave','defend_emerge','retreat_return','den_depart','hang_prepare','rage_pursue','edge_seek','edge_patrol','fight','fight_flee') and travel_speed>4 else (2 if state in ('tap','tap_prepare','contact','defend_hold','rage_scan','rage_recover','fight') else 0)][direction]
        if web_visible:
            # The silk remains in the chosen corner, even if the spider leaves.
            try:root.lift(silk)
            except tk.TclError:pass
        # Optional per-second numeric trace to diagnose Windows-specific motion.
        if os.environ.get('SPIDER_HANG_TRACE')=='1' and state in ('hang_prepare','hang_descend','hang_dwell','hang_ascend') and now>=hang_trace_at:
            hang_trace_at=now+.8
            try:
                LOG.parent.mkdir(parents=True,exist_ok=True)
                with (LOG.parent/'hanging_trace.txt').open('a',encoding='utf-8') as f:
                    f.write(f"{now:.2f} {state} spider=({x:.1f},{y:.1f}) anchor=({hang_anchor[0]:.1f},{hang_anchor[1]:.1f}) end=({hang_end[0]:.1f},{hang_end[1]:.1f})\n")
            except Exception:
                pass
        root.geometry(f'{side}x{side}+{round(x-side/2)}+{round(y-side/2)}')
        canvas.itemconfigure(item,image=photo)
        update_hanging_cord(photo)
        if social is not None:
            social.publish(x,y,size,state,
                           fight_peer_id if state in ('threat_display','fight') else '',
                           fight_start if state in ('threat_display','fight') else 0.)
        root.after(20,tick)
    root.after(100,tick);root.mainloop()
def launch_two_spiders():
    """Launch two independent instances near one another to demonstrate a duel."""
    import subprocess
    base=[sys.executable] if getattr(sys,'frozen',False) else [sys.executable,str(Path(__file__).resolve())]
    monitor_w=ctypes.windll.user32.GetSystemMetrics(0) if os.name=='nt' else 1920
    for fx in (.47-68./monitor_w,.47+68./monitor_w):
        env=os.environ.copy()
        env.update(SPIDER_START_X_FRAC=str(fx),SPIDER_START_Y_FRAC='.435',
                   SPIDER_RETREAT_IDLE_SEC='75',SPIDER_FIGHTS='1')
        if getattr(sys,'frozen',False):
            # PyInstaller one-file must unpack a fresh private runtime for each
            # child, otherwise the parent's temporary unpack directory vanishes.
            env['PYINSTALLER_RESET_ENVIRONMENT']='1'
            cwd=str(Path(sys.executable).resolve().parent)
        else:
            cwd=str(BASE)
        subprocess.Popen(base,env=env,cwd=cwd,
                         creationflags=(0x08000000 if os.name=='nt' else 0))

if __name__=='__main__':
    if '--duel' in sys.argv:
        launch_two_spiders()
        sys.exit(0)
    try:main()
    except Exception:
        show_error(traceback.format_exc())
        sys.exit(1)
