import os
import warnings
from numbers import Number
from os.path import join
from typing import List, Dict, Tuple, Union, Any

import openpyxl
import openpyxl.cell
import openpyxl.utils.exceptions
from openpyxl.workbook import Workbook
from openpyxl.worksheet._read_only import ReadOnlyWorksheet

from ccrev import config
from ccrev.config import WS_MEAN_ADDR, WS_STDEV_ADDR


class DataExtractor:
    def __init__(self):
        pass

    @staticmethod
    def get_data(
            data_source, col=None, min_row=None, max_row=None, worksheet_index=None, address=None
    ) -> Union[List, Any]:

        data = []
        try:
            worksheet_index = worksheet_index if worksheet_index else config.DATA_SHEET
            wb: Workbook = openpyxl.load_workbook(data_source, read_only=True, data_only=True)
            ws: ReadOnlyWorksheet = wb.worksheets[worksheet_index]

            for row in ws.iter_rows(min_col=col, max_col=col, min_row=min_row):  # returns Container{Cell]
                cell: openpyxl.cell.ReadOnlyCell = row[0]  # rows are one col wide; use first item
                if not cell.value:
                    warnings.warn(f'Empty cell in {data_source} at ({cell.column},{cell.row})')
                    # data.append(None)
                    break  # TODO should know max_row beforehand so don't have to rely on clean data
                if cell.row >= max_row:  # empty cells kill the script
                    break
                else:
                    data.append(cell.value)

        except openpyxl.utils.exceptions.InvalidFileException as e:
            # TODO handle CSV
            raise NotImplementedError('ccrev can only handle excel files.')

        return data

    @staticmethod
    def get_stats_data(data_source, worksheet_index=None) -> Dict[str, Number]:
        """
        returns cell values specified by WS_STDEV_ADDR and WS_MEAN_ADDR
        """
        ws = openpyxl.load_workbook(data_source, read_only=True, data_only=True).worksheets[worksheet_index]
        chart_stats: Dict[str, Number] = {
            config.ST_DEV: ws.cell(*WS_STDEV_ADDR).value,
            config.MEAN  : ws.cell(*WS_MEAN_ADDR).value,
        }

        return chart_stats

    @staticmethod
    def gen_files_from_dir(dir_path: str, file_types: Union[str, Tuple[str]]=None):
        for file in os.listdir(dir_path):
            file_in_dir = join(dir_path, file)
            if file_types and file.endswith(file_types):
                yield file_in_dir
            elif not file_types:
                yield file
            else:
                continue

# def process_chart(chart: ChartData, rules_to_check: Sequence[Type[rules.Rule]]) -> None:
#     """
#     main driver for the script
#     mutates parm chart's 'signals' attribute
#
#     chart.signals will be a list of rule numbers
#     that correspond to the violations of rules at the same index in chart.data
#     """
#
#     def get_signals(data: List[Number], rules_to_check, checker: rules.RuleChecker):
#         for rule in rules_to_check:
#             for data_index in range(len(data)):
#                 checker.check(rule, data_index)
#         pass
#
#     rule_checker = rules.RuleChecker()
#     rule_checker.chart = chart
#     get_signals(rule_checker.chart.data, rules_to_check, rule_checker)
