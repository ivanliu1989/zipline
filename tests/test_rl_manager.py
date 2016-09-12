from unittest import TestCase
import pandas as pd

from zipline.rl_manager import InMemoryRLManager, Restriction, RestrictionHistoryOverlapError

str_to_ts = lambda dt_str: pd.Timestamp(dt_str, tz='UTC')

class RlManagerTestCase(TestCase):

    def test_in_memory_rl_manager(self):
        restrictions = [
            Restriction(1, str_to_ts('2011-01-03'), str_to_ts('2011-01-05'), 'freeze'),
            Restriction(1, str_to_ts('2011-01-05'), str_to_ts('2011-01-07'), 'liquidate'),
            Restriction(2, str_to_ts('2011-01-03'), str_to_ts('2011-01-04'), 'liquidate'),
        ]

        imrlm = InMemoryRLManager(restrictions)

        self.assertEqual(imrlm.restriction(1, str_to_ts('2011-01-03')), 'freeze')
        self.assertEqual(imrlm.restriction(1, str_to_ts('2011-01-03 14:31')), 'freeze')
        self.assertEqual(imrlm.restriction(1, str_to_ts('2011-01-05')), 'liquidate')
        self.assertEqual(imrlm.restriction(1, str_to_ts('2011-01-07')), 'allowed')

        self.assertEqual(imrlm.is_restricted(1, str_to_ts('2011-01-03')), True)
        self.assertEqual(imrlm.is_restricted(1, str_to_ts('2011-01-03 14:31')), True)
        self.assertEqual(imrlm.is_restricted(1, str_to_ts('2011-01-05')), True)
        self.assertEqual(imrlm.is_restricted(1, str_to_ts('2011-01-07')), False)

    def test_in_memory_rl_manager_overlapping(self):
        restrictions = [
            Restriction(1, str_to_ts('2011-01-03'), str_to_ts('2011-01-05'), 'freeze'),
            Restriction(1, str_to_ts('2011-01-04'), str_to_ts('2011-01-07'), 'liquidate'),
        ]

        with self.assertRaises(RestrictionHistoryOverlapError):
            InMemoryRLManager(restrictions)
