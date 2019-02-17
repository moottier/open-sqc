from __future__ import annotations

import unittest

import ccrev.config
from ccrev.data_processor import DataExtractor
from ccrev import main
import itertools
from typing import List, Dict, Iterable

# paths to excel files used to validated script
from ccrev.main import Reviewer, REVIEWER_CONFIG

METTLER_CHART = r'H:\code\ccrev\test\TA by Mettler- Rondo 1.xlsx'
METHANOL_CHART = r'H:\code\ccrev\test\Methanol by GC.xlsx'
PH1_CHART = r'H:\code\ccrev\test\pH by Orion #1 pH Meter.xlsx'
PH2_CHART = r'H:\code\ccrev\test\pH by Orion #2 pH Meter.xlsx'

# list of paths for convenience only
PATHS = [
    METTLER_CHART,
    # METHANOL_CHART,
    PH1_CHART,
    # PH2_CHART,
]

# dictionary with keys equal to file paths
# key values are dictionaries with keys equal to a rule number
# values for rule numbers are data indexes or ranges of data indexes where a signal was found
# signals were determined by hand (looking over control chart point by point)
# used to validate the script
SIGNALS_BY_HAND = {
    METTLER_CHART: {
        1: [178, 262, 388, 447, 472, ],
        2: itertools.chain(  # chain creates single iterable from iterables args
            range(36, 49),
            range(85, 108),  # range objects are [inclusive, exclusive)
            range(110, 123),  # if excel data starts on row 2 then
            range(131, 155),  # range(36, 48) corresponds to data in excel rows 38-49
            range(165, 215),
            range(239, 253),
            range(270, 278),
            range(293, 301),
            range(372, 388),
            range(409, 417),
            range(423, 436),
            range(448, 472),
            range(479, 491),
            range(492, 504),
            range(522, 531),
            range(565, 574),
            range(578, 587),
            range(593, 605),
        ),
        3: range(619, 625),
        4: range(335, 349),
    },
    PH1_CHART: {
        1: [287, 672, 864, 1046, ],
        2: itertools.chain(
            range(17, 27),
            range(54, 65),
            range(79, 93),
            range(106, 120),
            range(122, 131),
            range(136, 146),
            range(150, 163),
            range(187, 197),
            range(199, 216),
            range(216, 231),
            range(231, 241),
            range(241, 255),
            range(265, 274),
            range(274, 283),
            range(311, 322),
            range(325, 333),
            range(334, 357),
            range(358, 378),
            range(274, 283),
            range(383, 393),
            range(393, 409),
            range(409, 422),
            range(422, 435),
            range(450, 479),
            range(481, 492),
            range(492, 501),
            range(513, 521),
            range(521, 534),
            range(534, 544),
            range(544, 552),
            range(554, 568),
            range(568, 582),
            range(585, 593),
            range(593, 606),
            range(606, 623),
            range(627, 644),
            range(644, 665),
            range(673, 681),
            range(684, 696),
            range(702, 714),
            range(723, 736),
            range(771, 783),
            range(796, 813),
            range(821, 834),
            range(843, 856),
            range(865, 873),
            range(880, 889),
            range(890, 901),
            range(906, 918),
            range(923, 934),
            range(949, 958),
            range(966, 982),
            range(986, 998),
            range(999, 1015),
            range(1026, 1040),
            range(1047, 1065),
            range(1073, 1087),
            range(1112, 1120),
        ),
        3: None,
        4: None,
    },
    # PH2_CHART: {
    #     1: ,
    #     2: ,
    #     3: ,
    #     4: ,    
    # },
}


def reformat_SIGNALS_BY_HAND(
        chart_signals: Dict[int, Iterable[int]],
        length: int
) -> List[int]:
    """
    convert the dicts nested in "SIGNALS_BY_HAND" from an iterable containing 
    data indexes that's keyed to the rule violation found at those indexes
    to a list of rule numbers

    use param 'length' to set length of new list
    0s represent data points that don't violate any rules
    lower rule numbers take precedence over higher numbers

    ex:

    PH_CHART {
        1: [1, 2, 4]
        2: [2, 4, 6]
        3: None
        4: [8,]
    } 

    is converted to

    [0, 1, 1, 0, 1, 0, 2, 0, 4, 0, 0]
    """
    reformatted_list = [0] * length

    for rule_number, data_indexes in chart_signals.items():
        if not data_indexes:
            pass
        else:
            for data_index in data_indexes:
                if reformatted_list[data_index] is 0 or rule_number < reformatted_list[data_index]:
                    reformatted_list[data_index] = rule_number
                else:
                    pass
    return reformatted_list


# class TestRulesIndividually(unittest.TestCase):
#     def setUp(self):
#         # list of rules for convenience
#         self.rules = [
#             rules.Rule1,
#             rules.Rule2,
#             rules.Rule3,
#             rules.Rule4,
#         ]
#
#         # dict with keys equal to file paths specified above
#         # values equal to openpyxl worksheet objects generated from those paths
#         worksheets = {
#             excel_file: main.get_data_sheet(excel_file) for excel_file in PATHS
#         }
#
#         # dict with keys equal to file paths specified above
#         # values data from worksheet objects in 'worksheets'
#         self.worksheet_data = {
#             excel_file: main.get_data(worksheet) for excel_file, worksheet in worksheets.items()
#         }
#
#         # dict with keys equal to file paths specified above
#         # values stats data from worksheet objects in 'worksheets'
#         self.stats_data = {
#             excel_file: main.get_stats_data(worksheet) for excel_file, worksheet in worksheets.items()
#         }
#
#     def _test_rule(self, rule_to_check: int):
#         for excel_file in PATHS:
#             # main.main() returns a dict
#
#             calculated_signals = main.main(
#                 data=self.worksheet_data[excel_file],
#                 stats_data=self.stats_data[excel_file],
#                 Rules=(self.rules[rule_to_check - 1],),
#                 DEBUG=True
#             )[excel_file]
#
#             reformatted_signals = reformat_SIGNALS_BY_HAND(SIGNALS_BY_HAND[excel_file], len(calculated_signals))
#
#             for signal_index, signal in enumerate(reformatted_signals):
#                 if signal is rule_to_check:
#                     with self.subTest(signal_index=signal_index):
#                         self.assertEqual(
#                             calculated_signals[signal_index].rule_number,
#                             reformatted_signals[signal_index],
#                             msg=f'File: {excel_file}'
#                         )
#
#     def test_rule1(self):
#         self._test_rule(1)
#
#     def test_rule2(self):
#         self._test_rule(2)
#
#     def test_rule3(self):
#         self._test_rule(3)
#
#     def test_rule4(self):
#         self._test_rule(4)


class TestDataProcessing(unittest.TestCase):
    """
    make sure no data is lost during data analysis, formatting, or reporting
    """
    def setUp(self):
        self.excel_files = [excel_file for excel_file in DataExtractor.gen_files_from_dir(ccrev.config.PATH)]
        self.reviewer = Reviewer(REVIEWER_CONFIG)
        # self.maxDiff = None

    def test_get_signals(self):
        for excel_file in self.excel_files:

            if excel_file in SIGNALS_BY_HAND.keys():
                chart_signals = main.get_signals(excel_file)
                chart_signals = [signal.rule_number for signal in chart_signals]
                signals_expected = reformat_SIGNALS_BY_HAND(SIGNALS_BY_HAND[excel_file], len(chart_signals))
                with self.subTest(excel_file=excel_file):
                    self.assertEqual(
                        chart_signals,
                        signals_expected                        
                        )



if __name__ == "__main__":
    unittest.main()
