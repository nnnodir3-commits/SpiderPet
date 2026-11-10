"""Run with py -m unittest test_v26_features.py"""
import json,tempfile,time,unittest,os
from pathlib import Path
from spider_windows import nearest_border,patrol_route,choose_nearby_window
from spider_peers import fight_phase,PeerRegistry

class TestWindowGeometry(unittest.TestCase):
    def test_border(self):
        self.assertEqual(nearest_border((100,100,400,300),230,110)[2],0)
        self.assertEqual(nearest_border((100,100,400,300),390,180)[2],1)
        self.assertEqual(nearest_border((100,100,400,300),120,290)[2],2)
    def test_corners_and_near_window(self):
        rect=(100,100,400,300)
        self.assertIn((400,100),patrol_route(rect,180,90))
        self.assertIn((100,300),patrol_route(rect,180,90))
        self.assertIsNotNone(choose_nearby_window([(123,rect)],180,90,65))
        self.assertIsNone(choose_nearby_window([(123,rect)],900,900,65))
class TestFight(unittest.TestCase):
    def test_two_actors_alternate(self):
        for elapsed in (1.,2.,3.,4.,5.,6.,7.):
            a=fight_phase(elapsed,0)
            b=fight_phase(elapsed,1)
            self.assertNotEqual(a[1],b[1])
        self.assertEqual(fight_phase(10.,0)[0],'finish')
    def test_registry_exchange(self):
        with tempfile.TemporaryDirectory() as temp:
            old=os.environ.get('LOCALAPPDATA')
            try:
                os.environ['LOCALAPPDATA']=temp
                a=PeerRegistry();b=PeerRegistry()
                a.publish(300,400,55,force=True)
                b.publish(410,430,55,force=True)
                self.assertEqual(a.scan(force=True)[0]['id'],b.id)
                a.close();b.close()
            finally:
                if old is None:os.environ.pop('LOCALAPPDATA',None)
                else:os.environ['LOCALAPPDATA']=old
if __name__=='__main__':unittest.main()
