"""Run: py -3 -m unittest test_v28_contact_gait.py"""
import math,unittest
from spider_combat import (duel_phase,winner_role,foot_contact_clearance,
                           strike_motion,gait_cycle_distance)

class ContactTests(unittest.TestCase):
    def test_target_gap(self):
        size=57.
        goal,vel=strike_motion((500.,300.),(500.,300.),(640.,300.),size,size,True,.50)
        self.assertAlmostEqual(640.-goal[0],foot_contact_clearance(size,size))
        self.assertGreater(vel,800.)
    def test_defender_holds_until_impact(self):
        for progress in (.0,.3,.53,.60):
            target,speed=strike_motion((640.,300.),(640.,300.),(510.,300.),57,57,False,progress)
            self.assertEqual(target,(640.,300.))
            self.assertEqual(speed,0.)
        target,speed=strike_motion((640.,300.),(640.,300.),(520.,300.),57,57,False,.71)
        self.assertGreater(target[0],640.)
        self.assertGreater(speed,0.)
    def test_gait_follows_body(self):
        size=57.
        slow=gait_cycle_distance(size,62)
        fast=gait_cycle_distance(size,250)
        self.assertLess(slow,size*1.40)
        self.assertGreater(fast,slow)
        self.assertLess(fast,size*1.60)
        self.assertLess(gait_cycle_distance(size,500,True),size*1.35)
    def test_duel_synchronized_roles(self):
        winner=winner_role('abc','xyz')
        for elapsed in (1.,2.,3.4,4.6,5.75,6.85):
            p0=duel_phase(elapsed,0,winner)
            p1=duel_phase(elapsed,1,winner)
            self.assertEqual(p0[0],p1[0])
            self.assertNotEqual(p0[1],p1[1])
    def test_live_simulated_contact(self):
        size=57.;dt=.02
        anchors=((430.,350.),(570.,350.))
        pos=[list(anchors[0]),list(anchors[1])]
        winner=0
        hits=[];min_dist=float('inf')
        beat=None;closest=float('inf')
        # Simulates independent participants with a 0.12s peer-position lag.
        history=[]
        for step in range(375):
            t=step*dt
            history.append((t,tuple(pos[0]),tuple(pos[1])))
            historical=history[max(0,step-6)]
            stage,_,_=duel_phase(t,0,winner)
            if stage!=beat:
                if beat in ('strike','finisher'):hits.append(closest)
                beat=stage;closest=float('inf')
            if stage in ('strike','finisher'):
                closest=min(closest,math.dist(pos[0],pos[1]))
            nextpos=[]
            for actor in (0,1):
                other=1-actor
                name,attacking,p=duel_phase(t,actor,winner)
                goal=pos[actor];speed=0.
                if name in ('strike','finisher'):
                    goal,speed=strike_motion(pos[actor],anchors[actor],historical[other+1],
                                             size,size,attacking,p,name=='finisher')
                elif name=='recover':
                    goal=anchors[actor];speed=270.
                dx=goal[0]-pos[actor][0];dy=goal[1]-pos[actor][1]
                d=math.hypot(dx,dy);move=min(d,speed*dt)
                nextpos.append([pos[actor][0]+dx/max(d,.00001)*move,
                                pos[actor][1]+dy/max(d,.00001)*move])
            pos=nextpos
        if beat in ('strike','finisher'):hits.append(closest)
        self.assertEqual(len(hits),6)
        # Every strike brings forelegs into the same small contact zone.
        self.assertTrue(all(d<size*.90 for d in hits),hits)
        # No fatal clipping of bodies during an impact.
        self.assertTrue(all(d>size*.32 for d in hits),hits)

if __name__=='__main__':unittest.main()
