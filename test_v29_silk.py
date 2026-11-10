"""Regression checks for the organic corner-web geometry."""
import math
import unittest
from spider_nest import (
    silk_paths, silk_segments, triangle_local, point_in_triangle,
    grown_span, max_web_span, INITIAL_SPAN, CANVAS_SIDE,
)

class OrganicSilkTests(unittest.TestCase):
    def test_all_nodes_remain_within_clickable_web(self):
        for corner in range(4):
            for span in (INITIAL_SPAN, max_web_span(1920,1080)):
                tri=triangle_local(corner,span,CANVAS_SIDE)
                paths=silk_paths(corner,span)
                self.assertGreater(len(paths),150)
                for points,width,role in paths:
                    self.assertGreater(len(points),1)
                    self.assertTrue(width>0)
                    for p in points:
                        self.assertTrue(point_in_triangle(p,tri,2.), (corner,p,role))
    def test_scallops_are_curved_not_square_cells(self):
        paths=silk_paths(0,350.)
        curved=[]
        for points,_,role in paths:
            if role!='scallop':continue
            a,b=points[0],points[-1]
            mid=points[len(points)//2]
            ideal=((a[0]+b[0])/2.,(a[1]+b[1])/2.)
            curved.append(math.dist(mid,ideal))
        self.assertGreater(len(curved),160)
        self.assertGreater(sum(v>1.0 for v in curved),100)
    def test_hub_does_not_move_when_large_web_grows(self):
        # Fifth support segment terminates in the fixed central hub.
        hubs=[]
        for sp in (INITIAL_SPAN,275.,360.,max_web_span(1920,1080)):
            paths=silk_paths(0,sp)
            hub=paths[4][0][-1]
            hubs.append(hub)
        for p in hubs[1:]:
            self.assertLess(math.dist(p,hubs[0]),0.1)
    def test_original_nest_region_remains_clickable_when_expanded(self):
        for span in (INITIAL_SPAN,max_web_span(1920,1080)):
            triangle=triangle_local(0,span)
            self.assertTrue(point_in_triangle((87.,87.),triangle))
        self.assertEqual(grown_span(0,1920,1080),INITIAL_SPAN)
        self.assertGreater(grown_span(300,1920,1080),INITIAL_SPAN*2.)
    def test_break_fibres_match_new_curved_paths(self):
        for corner in range(4):
            for span in (INITIAL_SPAN,440.):
                a=silk_paths(corner,span)
                b=silk_segments(corner,span)
                self.assertEqual(len(a),len(b))
                for (points,_,_), (start,end,_) in zip(a,b):
                    self.assertEqual(start,points[0])
                    self.assertEqual(end,points[-1])

if __name__=='__main__':unittest.main()
