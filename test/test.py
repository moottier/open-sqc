from __future__ import annotations

import itertools
import os
import unittest
from typing import List, Dict, Iterable

from ccrev import config
from ccrev.data_processing import DataExtractor
from ccrev.rule_checking import RuleChecker
from ccrev.rules import Rule1, Rule2, Rule3, Rule4

# TODO I use 'chart', 'file', and 'excel_file' pretty interchangeable. clean that up.
TEST_DATA_FILES = [
    r'H:\code\ccrev\test\TA by Mettler- Rondo 1.xlsx',
    # r'H:\code\ccrev\test\Methanol by GC.xlsx',
    r'H:\code\ccrev\test\pH by Orion #1 pH Meter.xlsx',
    # r'H:\code\ccrev\test\pH by Orion #2 pH Meter.xlsx',
]
TEST_DATA_FILES = [os.path.basename(file) for file in TEST_DATA_FILES]

# dictionary with keys equal to file paths
# key values are dictionaries with keys equal to a rule number
# values for rule numbers are data indexes or ranges of data indexes where a signal was found
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
            range(165, 215),  # range(36, 48) corresponds to excel rows 38-49
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
                if reformatted_list[data_index] is 0 or rule_number < reformatted_list[data_index]:
                    reformatted_list[data_index] = rule_number
                else:
                    pass
    return reformatted_list


class TestExcelDataExtractor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data_extractor = DataExtractor
        cls.excel_files = [excel_file for excel_file in
                           DataExtractor.gen_files(config.PATH, config.EXCEL_FILE_EXTENSIONS)]

    def test_gen_files_from_dir(self):
        expected_files = [file for file in os.listdir(config.PATH) if file.endswith(config.EXCEL_FILE_EXTENSIONS)]
        data_extractor_files = [os.path.basename(file) for file in self.excel_files]
        self.assertEqual(
            data_extractor_files,
            expected_files
        )

    def test_get_data(self):
        file_data_list = [
            self.data_extractor.get_excel_data(
                file,
                min_col=config.DATA_COL,
                max_col=config.DATA_COL,
                min_row=config.DATA_START_ROW,
                worksheet_index=config.DATA_SHEET,
            ) for file in self.excel_files]
        for file_data in file_data_list:
            self.assertIsInstance(
                file_data,
                List
            )
            self.assertTrue(all(isinstance(value, (float, int)) for value in file_data),
                            msg=f'{[val for val in file_data if not isinstance(val, float)]}')


class TestRuleChecker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rule_checker = RuleChecker(rules=(Rule1, Rule2, Rule3, Rule4))
        cls.excel_files = [os.path.basename(excel_file) for excel_file in
                           DataExtractor.gen_files(config.PATH, config.EXCEL_FILE_EXTENSIONS)]
        cls.data = [
            DataExtractor.get_excel_data(
                file,
                min_col=config.DATA_COL,
                max_col=config.DATA_COL,
                min_row=config.DATA_START_ROW,
                worksheet_index=config.DATA_SHEET,
            ) for file in cls.excel_files]
        cls.st_devs = [
            DataExtractor.get_excel_data(
                file,
                min_col=config.WS_STDEV_ADDR[1],
                max_col=config.WS_STDEV_ADDR[1],
                min_row=config.WS_STDEV_ADDR[0],
                max_row=config.WS_STDEV_ADDR[0],
                worksheet_index=config.DATA_SHEET,
            ) for file in cls.excel_files]
        cls.means = [
            DataExtractor.get_excel_data(
                file,
                min_col=config.WS_MEAN_ADDR[1],
                max_col=config.WS_MEAN_ADDR[1],
                min_row=config.WS_MEAN_ADDR[0],
                max_row=config.WS_MEAN_ADDR[0],
                worksheet_index=config.DATA_SHEET,
            ) for file in cls.excel_files]

        cls.file_data_map = {excel_file: data for excel_file, data in zip(cls.excel_files, cls.data)}
        cls.file_st_devs_map = {
            excel_file: st_dev for
            excel_file, st_dev in
            zip(cls.excel_files, cls.st_devs)
        }
        cls.file_means_map = {
            excel_file: mean for
            excel_file, mean in
            zip(cls.excel_files, cls.means)
        }

    def setUp(self):
        self.signals = []

    def test_check_all(self):
        for file, data in self.file_data_map.items():
            if file in TEST_DATA_FILES:
                stats_data = {
                    'mean': self.file_means_map[file],
                    'stdev': self.file_st_devs_map[file]
                }
                expected_signals = flatten_signals_dict(SIGNALS_BY_HAND[file], len(data))
                signals = self.rule_checker.check_all_rules(data, return_type=int, **stats_data)
                with self.subTest(file=file):
                    self.assertEqual(signals, expected_signals, msg='%s: failed' % file)


if __name__ == "__main__":
    unittest.main()
