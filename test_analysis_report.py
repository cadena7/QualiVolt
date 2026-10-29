import math
import unittest
from datetime import datetime, timedelta
from analysis_report import Analysis, percentile


class AnalysisTests(unittest.TestCase):
    def test_power_factor_undefined_and_total_direction(self):
        from reader import channel_value
        self.assertTrue(math.isnan(channel_value('Pfti+_Avg',-1)))
        self.assertEqual(channel_value('har03V1_Avg [V]',-1),-1)
        names=['Pt+_Avg [W]','Pt-_Avg [W]','Pfti+_Avg','Pftc+_Avg','Pfti-_Avg','Pftc-_Avg']
        rows=[[10,0,.9,-1,-1,-1],[0,20,-1,-1,.8,-1]]
        analysis=Analysis((names,[datetime(2026,1,1),datetime(2026,1,2)],rows))
        series=analysis.total_power_factors()
        self.assertEqual(len(series),1)
        self.assertEqual(series[0][0],'Total inductivo')
        self.assertEqual(series[0][1],[.9,.8])

    def test_zero_fundamental_display_preserves_amplitudes(self):
        names=['har01I2_Avg [A]']+[f'har{n:02}I2_Avg [A]' for n in range(2,50)]
        analysis=Analysis((names,[datetime(2026,1,1)],[[0]*49]))
        values,counts,unit,note=analysis.display_spectrum('I2')
        self.assertEqual(unit,'A')
        self.assertEqual(values,[0]*48)
        self.assertEqual(counts,[1]*48)
        self.assertIn('0 A',note)
        self.assertTrue(all(math.isnan(v) for v in analysis.spectrum('I2')[0]))
        analysis.rows[0][2]=2
        values,_,unit,_=analysis.display_spectrum('I2')
        self.assertEqual(values[1],2)
        self.assertEqual(unit,'A')

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
