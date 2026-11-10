import math,unittest
from spider_combat import (winner_role,duel_phase,DUEL_DURATION,escape_destination)
from spider_nest import (triangle_screen,triangle_local,point_in_triangle,
                         grown_span,max_web_span,INITIAL_SPAN,corner_index,
                         silk_segments,CANVAS_SIDE)

class TestDuels(unittest.TestCase):
    def test_winner_same_in_both_processes(self):
        for a,b in (('a123','z456'),('dde','ac8'),('135','246')):
            self.assertEqual(winner_role(a,b),winner_role(b,a))
    def test_each_actor_strikes_and_winner_finishes(self):
        winner=winner_role('a123','z456')
        who={0:False,1:False}
        for t in (1.0,2.1,3.4,4.4):
            for role in (0,1):
                stage,attacking,p=duel_phase(t,role,winner)
                self.assertEqual(stage,'strike')
                if attacking:who[role]=True
        self.assertTrue(all(who.values()))
        a=duel_phase(6.5,winner,winner)
        b=duel_phase(6.5,1-winner,winner)
        self.assertEqual(a[0],'finisher')
        self.assertTrue(a[1]);self.assertFalse(b[1])
        self.assertEqual(duel_phase(DUEL_DURATION+0.1,0,winner)[0],'finish')
    def test_loser_runs_away(self):
        for pos,enemy in (((600,400),(550,400)),((150,150),(225,150)),
                          ((1700,750),(1600,750)),((90,90),(160,160))):
            target=escape_destination(pos,enemy,(1920,1080),75,480)
            self.assertGreater(math.dist(target,enemy),math.dist(pos,enemy)+140.)
            self.assertGreater(math.dist(target,pos),180.)
            self.assertTrue(75<=target[0]<=1845)
            self.assertTrue(75<=target[1]<=1005)

class TestTriangleNest(unittest.TestCase):
    def test_corner_variants_and_body_inside(self):
        sw,sh=1920,1080
        for corner,den in enumerate(((87,87),(sw-87,87),(87,sh-87),(sw-87,sh-87))):
            tri=triangle_screen(corner,INITIAL_SPAN,sw,sh)
            self.assertTrue(point_in_triangle(den,tri),f'{corner}, {tri}, {den}')
            self.assertTrue(point_in_triangle(tri[0],tri))
            self.assertFalse(point_in_triangle((sw/2,sh/2),tri))
            self.assertEqual(corner_index(den,sw,sh),corner)
    def test_large_nest_clickable_away_from_centre(self):
        sw,sh=1920,1080
        small=triangle_screen(0,INITIAL_SPAN,sw,sh)
        large=triangle_screen(0,max_web_span(sw,sh),sw,sh)
        target=(250,140)
        self.assertFalse(point_in_triangle(target,small))
        self.assertTrue(point_in_triangle(target,large))
    def test_growth_to_five_or_six_times_area(self):
        sw,sh=1920,1080
        self.assertEqual(grown_span(0,sw,sh),INITIAL_SPAN)
        self.assertEqual(grown_span(30,sw,sh),INITIAL_SPAN)
        large=grown_span(1000,sw,sh)
        area_ratio=((large-16)/(INITIAL_SPAN-16))**2
        self.assertGreaterEqual(area_ratio,4.9)
        self.assertLessEqual(area_ratio,6.5)
        self.assertGreater(grown_span(85,sw,sh),INITIAL_SPAN)
        self.assertAlmostEqual(large,max_web_span(sw,sh))
    def test_silk_segments_conform_to_triangle(self):
        for c in range(4):
            triangle=triangle_local(c,350)
            for a,b,_ in silk_segments(c,350):
                self.assertTrue(point_in_triangle(a,triangle,1.),(c,a,triangle))
                self.assertTrue(point_in_triangle(b,triangle,1.),(c,b,triangle))

if __name__=='__main__':unittest.main()
