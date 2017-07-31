from unittest import TestCase, TestLoader
import pioi


class TestPIOI(TestCase):

    def test_compare_pitch(self):
        p1 = 'nbuocbbbnbtaacadnbr'
        p2 = 'acaaaoanbaaocpbnoabnoabnocbnonbhoonaa'
        expected = 3.0
        actual = pioi.compare_pitch(p1, p2)
        self.assertEqual(expected, actual)

    def test_compare_ioi(self):
        ioi1 = 'sRsLslslsRsLssRRRRsLsRs'
        ioi2 = 'lRLsRRsRsRlRlRsRlRsRRRlRsRlsRRRlRsRlRsRRRlRs'
        expected = 21.0
        actual = pioi.compare_ioi(ioi1, ioi2)
        self.assertEqual(expected, actual)

    def test_vector_score(self):
        score_dict = {'grillo.mid': (4.0, 98.0)}
        expected = {'grillo.mid': 121.60592090848209}
        actual = pioi.vector_score(score_dict)
        self.assertEqual(expected, actual)

    def test_run(self):
        actual = pioi.run('schub01.mid', 'music_files')
        expected = {'grillo.mid': 121.60592090848209}
        self.assertEqual(expected, actual)

PIOI_SUITE = TestLoader().loadTestsFromTestCase(TestPIOI)
