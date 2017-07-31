from unittest import TestCase, TestLoader
import midiparser


class TestMidiParser(TestCase):

    def test_ioi_contour(self):
        durations = [4.0, 2.0, 2.0, 3.0, 1.0, 1.0, 1.0, 2.0, 4.0, 2.0]
        expected = 'sRRsRRlls'
        actual = midiparser.ioi_contour(durations)
        self.assertEqual(expected, actual)

    def test_directed_mod12(self):
        intervals = ['5', '0', '-2', '-2', '-1', '-2', '-2', '2', '0', '-2']
        expected = 'faoonoocao'
        actual = midiparser.directed_mod12(intervals)
        self.assertEqual(expected, actual)

    def test_to_midi(self):
        name = 'C4'
        expected = 60
        actual = midiparser.to_midi(name)
        self.assertEqual(expected, actual)

    def test_process_file(self):
        file = 'schub01.mid'
        expected = (
            ['RsLslslsRsLslslsRsLssRRRRsLsRsLssRRRRsLssRRRRsLsRRsLslslsRsLslslsRsLssRRRRsLsRsLssRRRRsLssRRRRsLsRRsLslslslslRSRRRRsLssRRRRsLsRRsLslslslslRSRRRRsLssRRRRsL'],
            ['aacadncsaacadnbpaaaonbccbnqaaaoocccbnbuocbbbnbtaacadnbraacadocpaaaonbccbnqcacooocccbnbuocbbbnbtaabacacacacbcccbnbuocbbbnbtaabafanacacbcccbnbuocbbbnb'])
        actual = midiparser.process_file(file)
        self.assertEqual(expected, actual)

MIDIPARSER_SUITE = TestLoader().loadTestsFromTestCase(TestMidiParser)
