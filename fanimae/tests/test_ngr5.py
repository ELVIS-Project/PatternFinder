from unittest import TestCase, TestLoader
import ngr5


class TestNGR5(TestCase):

    def test_get_ngrams(self):
        file_info = 'apacabacaaaoanbaaaaapacab'
        expected = ['acaaa', 'cabac', 'aoanb', 'apaca', 'acaba', 'aaaap',
                    'aaaoa', 'abaca', 'bacaa', 'anbaa', 'aapac', 'oanba',
                    'baaaa', 'pacab', 'aaapa', 'aaaaa', 'caaao', 'nbaaa',
                    'aaoan']
        actual = ngr5.get_ngrams(file_info)
        self.assertEqual(expected, actual)

    def test_compare(self):
        ngrams = ['acaaa', 'cabac', 'aoanb', 'apaca', 'acaba', 'aaaap']
        ngrams2 = ['acaaa', 'cabac', 'baaaa', 'pacab', 'aaapa', 'aaaaa']
        expected = 2
        actual = ngr5.compare(ngrams, ngrams2)
        self.assertEqual(expected, actual)

    def test_run(self):
        expected = {'grillo.mid': 1}
        actual = ngr5.run('schub01.mid', 'music_files')
        self.assertEqual(expected, actual)

NGR5_SUITE = TestLoader().loadTestsFromTestCase(TestNGR5)
