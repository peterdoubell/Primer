import unittest

try:
    import numpy as np
    from tools.anatomy_sources.build_massp_joint_interfaces import region_interfaces,build_label_surfaces,SCALE
    AVAILABLE=True
except ImportError:
    AVAILABLE=False


@unittest.skipUnless(AVAILABLE,'Optional scientific source mesh dependencies')
class JointLabelInterfaces(unittest.TestCase):
    def test_two_labels_have_the_known_barycentric_halfway_plane(self):
        triangles=np.array(region_interfaces((0,0,0,1),0),dtype=float)/SCALE
        self.assertGreater(len(triangles),0)
        np.testing.assert_allclose(triangles[:,:,2],.5)
        self.assertTrue(np.all(triangles.sum(2)<=1+1e-12))

    def test_four_class_interfaces_retain_face_and_tetrahedron_junctions(self):
        vertices=np.array(region_interfaces((0,1,2,3),0)).reshape(-1,3)
        for point in ((6,0,0),(4,4,0),(4,0,4),(3,3,3)):
            self.assertTrue(np.any(np.all(vertices==point,axis=1)))

    def test_every_emitted_triangle_is_a_maximum_weight_interface(self):
        for pattern in ((0,0,1,1),(0,1,2,3),(0,1,0,2),(0,0,0,1)):
            for target in set(pattern):
                for tri in region_interfaces(pattern,target):
                    center=np.mean(tri,axis=0)/SCALE
                    bary=np.r_[1-center.sum(),center]
                    weights={code:float(bary[np.array(pattern)==code].sum()) for code in set(pattern)}
                    self.assertAlmostEqual(weights[target],max(weights.values()),places=12)
                    self.assertTrue(any(code!=target and abs(value-weights[target])<1e-12 for code,value in weights.items()))

    def test_all_fifteen_vertex_label_patterns_share_identical_opposite_interfaces(self):
        from itertools import product
        from collections import defaultdict
        patterns=set()
        for raw in product(range(4),repeat=4):
            canonical={code:i for i,code in enumerate(dict.fromkeys(raw))}
            patterns.add(tuple(canonical[code] for code in raw))
        self.assertEqual(len(patterns),15)
        for pattern in patterns:
            interfaces=defaultdict(list)
            for target in set(pattern):
                for triangle in region_interfaces(pattern,target):
                    interfaces[tuple(sorted(triangle))].append(np.array(triangle))
            for copies in interfaces.values():
                self.assertEqual(len(copies),2)
                normals=[np.cross(tri[1]-tri[0],tri[2]-tri[0]) for tri in copies]
                np.testing.assert_array_equal(normals[0],-normals[1])

    def test_original_label_values_and_distinct_neighbour_classes_are_preserved(self):
        labels=np.zeros((5,5,5),dtype=int)
        labels[2,2,2]=9;labels[3,2,2]=11;labels[2,3,2]=38
        original=labels.copy()
        surfaces,_=build_label_surfaces(labels,{9,11,38})
        np.testing.assert_array_equal(labels,original)
        self.assertEqual(set(surfaces),{9,11,38})
        self.assertTrue(all(len(faces)>0 for _,faces in surfaces.values()))


if __name__=='__main__':unittest.main()
