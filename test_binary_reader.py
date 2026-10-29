"""Pruebas del lector y comparación opcional con las grabaciones locales."""
import tempfile
import unittest
from pathlib import Path
from binary_reader import load_binary, channel_layout, read_header
from reader import load_csv


class BinaryTests(unittest.TestCase):
    def test_layout(self):
        channels = [c for c in channel_layout() if c]
        self.assertEqual(len(channels), 534)
        self.assertEqual(len(set(channels)), 534)

    def test_invalid_header(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'invalid.HED'
            path.write_bytes(b'not a recording')
            with self.assertRaises(ValueError):
                read_header(path)

    def test_real_recordings(self):
        paths = list((Path(__file__).parent / 'files').glob('*.HED'))
        if not paths:
            self.skipTest('No hay grabaciones locales')
        for path in paths:
            with self.subTest(path=path.name):
                names, times, values = load_binary(path)
                self.assertEqual(len(names), 566)
                self.assertEqual(len(values), read_header(path)['registros'])
                self.assertEqual(len(times), len(values))
                if path.with_suffix('.csv').exists():
                    csv_names, csv_times, csv_values = load_csv(path.with_suffix('.csv'))
                    self.assertEqual(times, csv_times)
                    indices = [csv_names.index(n) for n in names]
                    for row, reference in zip(values, csv_values):
                        for actual, index in zip(row, indices):
                            if csv_names[index].startswith(('Ea','Er','Es')):
                                self.assertAlmostEqual(actual, reference[index], delta=1e-7+abs(reference[index])*1e-6)
                            else:
                                self.assertAlmostEqual(actual, reference[index], places=8)
                with tempfile.TemporaryDirectory() as directory:
                    copy = Path(directory)/'renamed.HED'
                    copy.write_bytes(path.read_bytes())
                    payload = path.with_suffix('.PER').read_bytes()
                    copy.with_suffix('.PER').write_bytes(payload[:-512])
                    with self.assertRaises(ValueError):
                        load_binary(copy)
                    copy.with_suffix('.PER').write_bytes(payload)
                    self.assertEqual(load_binary(copy)[1], times)


if __name__ == '__main__':
    unittest.main()
