import unittest
import math
from retreat_activity import departure_waypoint,retreat_is_due
from retreat_lifecycle import RetreatLifecycle

class TestActiveRetreat(unittest.TestCase):
    def test_departure_exits_den_vicinity_for_all_corners(self):
        for w,h in ((1920,1080),(1366,768),(1024,768)):
            margin=87
            for den in ((margin,margin),(w-margin,margin),(margin,h-margin),(w-margin,h-margin)):
                for angle in (-.48,0,.48):
                    pt=departure_waypoint(den,w,h,75,72,jitter=angle,excursion=250)
                    self.assertGreater(math.dist(den,pt),72+35)
                    self.assertTrue(75<=pt[0]<=w-75)
                    self.assertTrue(75<=pt[1]<=h-75)
    def test_no_immediate_return_after_departure(self):
        self.assertFalse(retreat_is_due(31,0,18,70))
        self.assertTrue(retreat_is_due(71,0,18,70))
        self.assertFalse(retreat_is_due(71,60,18,70))
    def test_retreat_preserves_and_fades(self):
        home=RetreatLifecycle(abandon_after=300,fade_seconds=30,vicinity_radius=72)
        home.plan((100,100));home.start_build();home.finish(0)
        self.assertEqual(home.update(5,(110,110)),1.)
        self.assertEqual(home.update(10,(250,250)),1.)
        self.assertAlmostEqual(home.update(325,(250,250)),.5)
        self.assertEqual(home.status,'fading')
        self.assertEqual(home.update(328,(105,105)),1.)
        self.assertEqual(home.status,'ready')
        self.assertEqual(home.update(329,(250,250)),1.)
        self.assertAlmostEqual(home.update(644,(250,250)),.5)
        self.assertEqual(home.update(659,(250,250)),0.)
        self.assertFalse(home.exists)

if __name__=='__main__': unittest.main()
