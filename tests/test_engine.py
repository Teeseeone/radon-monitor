"""Run with python -m unittest discover -s tests -v (no HA required)."""
import importlib.util
from pathlib import Path
import unittest
from datetime import datetime, timedelta, timezone
spec = importlib.util.spec_from_file_location('engine', Path(__file__).parents[1] / 'custom_components/radon_monitor/engine.py')
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)
SETTINGS = {'warning':100,'high':200,'recovery':80,'delay_hours':2,'recovery_hours':6,'problem_hours':2}
NOW = datetime(2026, 10, 3, tzinfo=timezone.utc)


class AverageTests(unittest.TestCase):
    def test_units(self):
        self.assertEqual(e.concentration('2','pCi/L'),74)
        self.assertEqual(e.concentration('0','Bq/m³'),0)

    def test_invalid_not_zero(self):
        for value in ['unknown','unavailable','nan','inf',-1,None]:
            self.assertIsNone(e.concentration(value,'Bq/m³'))
        self.assertIsNone(e.concentration(10,'ppm'))

    def test_month_and_year_windows(self):
        self.assertEqual(e.window_start(NOW,'6_months').month,4)
        self.assertEqual(e.window_start(NOW,'1_year').year,2025)
        self.assertEqual(e.window_start(NOW,'2_years').year,2024)
        leap=datetime(2024,2,29,tzinfo=timezone.utc)
        self.assertEqual(e.window_start(leap,'1_year').day,28)

    def test_weighting_window_edges(self):
        start=NOW+timedelta(minutes=30)
        rows=[{'start':NOW.timestamp(),'mean':10},{'start':(NOW+timedelta(hours=1)).timestamp(),'mean':40}]
        result=e.average(rows,start,NOW+timedelta(hours=2))
        self.assertEqual(result['value'],30)
        self.assertFalse(result['partial'])

    def test_gap_coverage(self):
        rows=[{'start':NOW.timestamp(),'mean':40},{'start':(NOW+timedelta(hours=2)).timestamp(),'mean':80}]
        result=e.average(rows,NOW,NOW+timedelta(hours=4))
        self.assertEqual(result['value'],60)
        self.assertEqual(result['bucket_coverage_percent'],50)
        self.assertTrue(result['partial'])

    def test_no_data(self):
        result=e.average([],NOW,NOW+timedelta(days=365))
        self.assertIsNone(result['value'])
        self.assertEqual(result['recorded_hours'],0)

    def test_duplicate_invalid_future_rows(self):
        row={'start':NOW.timestamp(),'mean':10}
        result=e.average([row,row,{'start':NOW.timestamp()+3600,'mean':None},{'start':NOW.timestamp()+10000,'mean':200}],NOW,NOW+timedelta(hours=2))
        self.assertEqual(result['value'],10)
        self.assertEqual(result['recorded_hours'],1)


class AlertTests(unittest.TestCase):
    def setUp(self):
        self.a=e.AlertState()

    def update(self,hours,value):
        return self.a.update(100000+hours*3600,value,SETTINGS)

    def test_elevated_persistence_and_no_spam(self):
        self.assertEqual(self.update(0,100),('elevated',[]))
        self.assertEqual(self.update(1,110)[1],[])
        self.assertEqual(self.update(2,110)[1],['elevated'])
        self.assertEqual(self.update(3,110)[1],[])

    def test_high_escalation_independent_timer(self):
        self.update(0,120)
        self.update(2,120)
        self.update(3,200)
        self.assertEqual(self.update(4,220)[1],[])
        self.assertEqual(self.update(5,220)[1],['high'])

    def test_high_direct(self):
        self.update(0,220)
        self.assertEqual(self.update(2,220)[1],['high'])

    def test_invalid_breaks_threshold_timer(self):
        self.update(0,220)
        self.update(1,None)
        self.assertEqual(self.update(2,220)[1],[])
        self.assertEqual(self.update(4,220)[1],['high'])

    def test_problem_and_restore_once(self):
        self.update(0,None)
        self.assertEqual(self.update(2,None)[1],['sensor_problem'])
        self.assertEqual(self.update(3,None)[1],[])
        self.assertEqual(self.update(4,36)[1],['sensor_restored'])
        self.assertEqual(self.update(5,36)[1],[])

    def test_recovery_hysteresis(self):
        self.update(0,220)
        self.update(2,220)
        self.update(3,79)
        self.update(8,80) # equality breaks recovery
        self.update(9,79)
        self.assertEqual(self.update(14,79)[1],[])
        self.assertEqual(self.update(15,79)[1],['recovered'])

    def test_short_spike_resets(self):
        self.update(0,110)
        self.update(1,99)
        self.update(2,110)
        self.assertEqual(self.update(3,110)[1],[])

    def test_normal_watch_boundaries(self):
        self.assertEqual(self.update(0,79)[0],'normal')
        self.assertEqual(self.update(1,80)[0],'watch')
        self.assertEqual(self.update(2,200)[0],'high')

    def test_persisted_alert_avoids_repeat(self):
        self.update(0,220)
        self.update(2,220)
        restored=e.AlertState(self.a.data)
        self.assertEqual(restored.update(200000,220,SETTINGS)[1],[])


if __name__=='__main__':
    unittest.main()


class WeeklyTrendTests(unittest.TestCase):
    def rows(self, previous, current):
        return [{"start": (NOW-timedelta(hours=336-i)).timestamp(), "mean": previous if i<168 else current} for i in range(336)]

    def test_adjacent_weeks(self):
        for previous,current,direction in [(20,30,"rising"),(30,20,"falling"),(20,20,"steady"),(10,0,"falling")]:
            result=e.weekly_trend(self.rows(previous,current),NOW)
            self.assertEqual(result["direction"],direction)
            self.assertEqual(result["change"],current-previous)
            self.assertEqual(result["previous_average"],previous)

    def test_missing_history(self):
        for rows in [[],self.rows(20,30)[168:],self.rows(20,30)[20:]]:
            result=e.weekly_trend(rows,NOW)
            self.assertEqual(result["direction"],"unavailable")
            self.assertIsNone(result["change"])
