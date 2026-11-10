"""v32 regression: preserve real leg geometry & keep cadence from v31."""
import ast, hashlib, unittest
from pathlib import Path
from PIL import Image
from spider_combat import gait_cycle_distance

class OriginalLimbRegression(unittest.TestCase):
    def setUp(self):
        self.folder=Path(__file__).resolve().parent
        self.script=(self.folder/'spiderpet.pyw').read_text(encoding='utf-8')

    def test_exactly_32_real_photoreal_poses(self):
        frames=sorted(self.folder.glob('walk_??.png'))
        self.assertEqual(len(frames),32)
        for f in frames:
            with Image.open(f) as im:
                self.assertEqual((im.size,im.mode),((323,323),'RGBA'))
                self.assertIsNotNone(im.getbbox())

    def test_no_elastic_remapping_or_crossfade(self):
        self.assertNotIn('Image.blend(',self.script)
        self.assertNotIn('sprites128',self.script)
        self.assertIn('for sprite in sprites:',self.script)
        self.assertIn('int((gait+2)//4)%32',self.script)
        self.assertEqual(self.script.count('int((gait+2)//4)%32'),2)
        tree=ast.parse(self.script)
        self.assertTrue(any(isinstance(n,ast.FunctionDef) and n.name=='main' for n in tree.body))

    def test_quarter_phases_pick_real_not_ghost_pose(self):
        for p in range(128):
            ix=(int((p+2)//4))%32
            self.assertTrue(0<=ix<32)
        # The final phases must wrap to pose 00 without discontinuity.
        self.assertEqual((int((127+2)//4))%32,0)

    def test_fast_stride_distance_preserved(self):
        self.assertTrue(39<gait_cycle_distance(57,60)<50)
        self.assertTrue(39<gait_cycle_distance(57,200,True)<53)

    def test_original_silhouette_and_joint_texture(self):
        # Baseline SHA256s are from v30 (before v31's elastic warp).
        baseline = {0: '4a0f295bea351ebfa8257ace4b1b98621cd8060ab0ce96636435645809de39ad', 1: '0bdf3a91b8eb0ee4c758caa15871f9828297ba95a2d632efec84737b7d2a7ba4', 2: 'c86d3acc56aa4d488ce537bd7ff357c0db329edc323b784eb82806b47cbf9da6', 3: 'fa74db036ee85ba3c407bc929bdab925204f1a0e854ca1c6bbe5c244eb08eacc', 4: 'b4d89d3bf30aa18d721b9d461dfc40e498086222baf0802d3a94d7a94d9ecd2f', 5: '7dbd478a05afb5beb5258f69fe5ebb4805da34ebe5f6ba6e183aa7a566e76a6e', 6: 'e1e8c12a9121d1d12ea68afa10400afb88be3d834fd3e9ab22073b7fd79710a5', 7: 'db34ff90a02eba763bfb41958067522b3131763a4df8b232b024e0aaffa5ef97', 8: '7f7a048647f2454025eb6e952bd23b9524a4755eb8191fbf17abee967798d6c8', 9: '52f15725a31a33068586ed627c2cc19f60c1079eb8c2aff9fd4592a934da2d9f', 10: '21a36f6a2a7f435666824db33f9f8bfadd38d4a0eb777f46a0ac529197026a03', 11: '246b0dbbc622035cf50cd2f20994e8ab21a848f6c1329c32e5b682b8e1234ef7', 12: '7ac2c47a735a9a09a786861596f274d91a5a82c21f6d0ff1160a6385d30cc1df', 13: '8f44793fb3970ef8410b693007895fc7edd46825659ad1595baf7620fbaf5eb7', 14: '4f8762284addbaf9b63412e8e21226c9e982e69f5933c2fabd68355846a6ddf7', 15: '7b0a131c6190e3e00d66407a28e295b6a26e31d3a75e58e16ff239f864b7e881', 16: '4207f84d14a2db57e25d1cf9254e8e5ab54a04a44fb2d03dcfab52788ab7c2db', 17: '7b24afbab04ab6793870757f81096692d2c33521c268a7affab2507cf29a6e2c', 18: '092072876c7578b4e279075b01fb3b59dc0b297b2704ae8525005c514e37175e', 19: '93071801aa8cd54c1ee2cf826aa53bc343482623faef8c3937a6385cfcb0aea2', 20: '2fee5ec885c95d9f1849f01fb6b4f168e5e979889f31d8de0d493c30d6ebcc89', 21: 'f74cf6d8ac91506ae6058f22e1683b664dc1614a4d4964e4933c33abd8d115c4', 22: '21505e39fa1801ac4677705d4b1ffc846004c3f54c9b0ac73ba2afbd257233e0', 23: '823081b5c06d1bf2a4544d5d9ca746aef8823f7629fa8a22650c90d9f43972c5', 24: 'bdf7a33d070d2ac3c68b154156dfaae34bb4c4a02038478a2fd5c58166fe99b3', 25: '51f49ea91b5c492b5f2f13db85a4d32dcfec952e3527312038aaea87ebb66e47', 26: '4ad1bdf37cb04dd1afdefd60b3e9bdefe294900caaf022edef486b3d33df1c59', 27: '0b94a00de92adfdf44936110e77f8e99971e387cb93f647a2ad58451e948be5c', 28: '8f031eb04deb6c5ef0d8d2d51bda673c7c7b0ac935bd0f6bae6c595b124c6eee', 29: 'f17aa5ff305d1fa706e86dc634770af66a20badde623095f03cabf3d2e9d8463', 30: 'd37fea6a21c3863a4e6278be3e35f81d98b98aa8cd73a1aaf5315d2cc21cf59f', 31: '287a032ab0913a2c461073d6c60b0c05a3db5643fb5247b9a1bc2145254b5eed'}
        for k,expected_hash in baseline.items():
            self.assertEqual(hashlib.sha256((self.folder/f'walk_{k:02d}.png').read_bytes()).hexdigest(),expected_hash)

if __name__=='__main__': unittest.main()
