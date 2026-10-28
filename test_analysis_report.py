import math
import unittest
from datetime import datetime, timedelta
from analysis_report import Analysis, percentile


class AnalysisTests(unittest.TestCase):
    def test_percentile(self):
        self.assertEqual(percentile([0,10], .95), 9.5)
        self.assertIsNone(percentile([], .95))

    def test_invalid_magnitudes_and_pairwise_spectrum(self):
        names=['har01V1_Avg [V]', 'har03V1_Avg [V]', 'thdV1_Avg [%]']
        rows=[[10,1,5], [0,100,-1], [20,2,7], [30,-1,math.nan]]
        times=[datetime(2026,1,1)+timedelta(minutes=i) for i in range(4)]
        analysis=Analysis((names,times,rows))
        values,counts=analysis.spectrum('V1')
        self.assertAlmostEqual(values[1],10)
        self.assertEqual(counts[1],2)
        self.assertTrue(math.isnan(values[0]))
        stats=analysis.stats('thdV1_Avg [%]')
        self.assertEqual(stats[1],6)
        self.assertEqual(stats[4],2)
        self.assertEqual(rows[1][2],-1)


if __name__ == '__main__':
    unittest.main()
