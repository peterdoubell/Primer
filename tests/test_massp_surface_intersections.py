import unittest

try:
    import numpy as np
    from tools.anatomy_sources.audit_massp_surface_intersections import triangle_contact, allowed_shared_contact, candidate_pairs
    AVAILABLE=True
except ImportError:
    AVAILABLE=False


@unittest.skipUnless(AVAILABLE,'Optional scientific geometry dependencies')
class TriangleContacts(unittest.TestCase):
    def setUp(self):
        self.first=np.array([[0.,0,0],[2.,0,0],[0.,2,0]])

    def test_nonadjacent_crossing_segment_is_detected(self):
        second=np.array([[.5,.5,-1],[.5,.5,1],[1.5,.5,0]])
        points=triangle_contact(self.first,second)
        self.assertFalse(allowed_shared_contact(points,np.empty((0,3))))
        np.testing.assert_allclose(sorted(points,key=lambda p:p[0]),[[.5,.5,0],[1.5,.5,0]])

    def test_a_shared_vertex_does_not_hide_a_crossing_beyond_it(self):
        second=np.array([[0.,0,0],[1.,1,-1],[1.,1,1]])
        self.assertFalse(allowed_shared_contact(triangle_contact(self.first,second),self.first[:1]))

    def test_expected_single_vertex_contact_is_allowed(self):
        second=np.array([[0.,0,0],[-1.,0,-1],[-1.,1,1]])
        self.assertTrue(allowed_shared_contact(triangle_contact(self.first,second),self.first[:1]))

    def test_coplanar_shared_edge_has_no_extra_contact(self):
        second=np.array([[0.,0,0],[2.,0,0],[1.,-1,0]])
        self.assertTrue(allowed_shared_contact(triangle_contact(self.first,second),self.first[:2]))

    def test_coplanar_overlap_beyond_a_shared_edge_is_rejected(self):
        second=np.array([[0.,0,0],[2.,0,0],[1.,1,0]])
        self.assertFalse(allowed_shared_contact(triangle_contact(self.first,second),self.first[:2]))

    def test_parallel_separated_triangles_do_not_intersect(self):
        self.assertEqual(triangle_contact(self.first,self.first+np.array([0,0,1.])),[])

    def test_reflection_preserves_crossing_classification(self):
        second=np.array([[.5,.5,-1],[.5,.5,1],[1.5,.5,0]])
        reflection=np.array([-1.,1,1])
        self.assertFalse(allowed_shared_contact(triangle_contact(self.first*reflection,second*reflection),np.empty((0,3))))

    def test_broad_phase_does_not_omit_any_intersecting_test_pair(self):
        triangles=np.array([self.first,[[.5,.5,-1],[.5,.5,1],[1.5,.5,0]],self.first+[0,0,2],self.first+[10,0,0]])
        pairs={tuple(p) for p in candidate_pairs(triangles)}
        self.assertIn((0,1),pairs)
        for a in range(len(triangles)):
            for b in range(a+1,len(triangles)):
                if triangle_contact(triangles[a],triangles[b]):self.assertIn((a,b),pairs)


if __name__=='__main__':unittest.main()
