from __future__ import annotations

import itertools
import os
import unittest
from typing import List, Dict, Iterable

from ccrev import config
from ccrev.extractor import DataExtractor
from ccrev.reviewer import Reviewer

# TODO I use 'chart', 'file', and 'excel_file'
#  pretty interchangeable. clean that up.
TEST_DATA_FILES = [
    r'H:\code\ccrev\test\TA by Mettler- Rondo 1.xlsx',
    # r'H:\code\ccrev\test\Methanol by GC.xlsx',
    r'H:\code\ccrev\test\pH by Orion #1 pH Meter.xlsx',
    # r'H:\code\ccrev\test\pH by Orion #2 pH Meter.xlsx',
]
TEST_DATA_FILES = [os.path.basename(file) for file in TEST_DATA_FILES]

# dictionary with keys equal to file paths
# key values are dictionaries with keys equal to a rule number
# values for rule numbers are data indexes or ranges of
# data indexes where a signal was found
# signals were determined by hand (looking over control chart point by point)
# used to validate the script
SIGNALS_BY_HAND = {
    TEST_DATA_FILES[0]: {
        1: [178, 262, 388, 447, 472, ],
        2: itertools.chain(  # chain creates single iterable from iterables args
                range(36, 49),
                range(85, 108),  # range objects are [inclusive, exclusive)
                range(110, 123),  # if excel data starts on row 2 then
                range(131, 155),  # excel rows 38-49 correspond to range(36, 48)
                range(165, 178),
                range(179, 215),
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
    TEST_DATA_FILES[1]: {
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
}


def flatten_signals_dict(
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
                if reformatted_list[data_index] == 0 or \
                        rule_number < reformatted_list[data_index]:
                    reformatted_list[data_index] = rule_number
                else:
                    pass
    return reformatted_list


class TestExcelDataExtractor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data_extractor = DataExtractor()
        cls.excel_files = [
            excel_file for excel_file in
            DataExtractor.gen_files(config.PATH, config.EXCEL_FILE_EXTENSIONS)
        ]
        for file in cls.excel_files:
            cls.data_extractor.add_workbook(file)

    def test_gen_files_from_dir(self):
        expected_files = [
            file for file in os.listdir(config.PATH)
            if file.endswith(config.EXCEL_FILE_EXTENSIONS)
        ]
        data_extractor_files = [
            os.path.basename(file) for file in self.excel_files
        ]
        self.assertEqual(
                data_extractor_files,
                expected_files
        )

    def test_never_gen_None(self):
        for wb_title in self.data_extractor.workbooks.keys():
            with self.subTest(wb_title=wb_title):
                data_reg = (
                    config.DATA_START_ROW, None,
                    config.DATA_COL, config.DATA_COL
                )
                dt_reg = (
                    config.DATA_START_ROW, None,
                    config.DATETIME_COL, config.DATETIME_COL
                )
                date_reg = (
                    config.DATA_START_ROW, None,
                    config.DATE_COL, config.DATE_COL
                )
                time_reg = (
                    config.DATA_START_ROW, None,
                    config.TIME_COL, config.TIME_COL
                )

                data_args = wb_title, *data_reg, config.DATA_SHEET
                dt_args = wb_title, *dt_reg, config.DATA_SHEET
                date_args = wb_title, *date_reg, config.DATA_SHEET
                time_args = wb_title, *time_reg, config.DATA_SHEET

                iters = zip(
                        self.data_extractor.gen_items_in_region(*data_args),
                        self.data_extractor.gen_items_in_region(*dt_args),
                        self.data_extractor.gen_items_in_region(*date_args),
                        self.data_extractor.gen_items_in_region(*time_args),
                )
            for idx, iter_vals in enumerate(iters):
                self.assertNotIn(None, iter_vals)


class TestRuleChecker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reviewer = Reviewer(**config.REVIEWER_KWARGS)
        cls.reviewer.add_charts(
                config.TEST_DIR,
                config.IChart
        )
        cls.reviewer.load_all_data()

    def setUp(self):
        self.signals = []

    def test_check_all(self):
        self.reviewer.check_all_rules()
        files = self.reviewer.chart_src_files
        signals = [chart.signals for chart in self.reviewer.control_charts]
        for file, signals in zip(files, signals):
            file = os.path.basename(file)
            if file in TEST_DATA_FILES:
                signals_by_hand = SIGNALS_BY_HAND[file]
                data_len = len(signals)
                expected = flatten_signals_dict(signals_by_hand, data_len)
                with self.subTest(file=file):
                    self.assertEqual(
                            signals,
                            expected,
                            msg='%s: failed' % file
                    )


if __name__ == "__main__":
    unittest.main()
