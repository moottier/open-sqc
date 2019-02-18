import os
from os.path import join
from typing import List, Tuple, Union, Any, Generator

import openpyxl
import openpyxl.cell
import openpyxl.utils.exceptions
from openpyxl.workbook import Workbook
from openpyxl.worksheet._read_only import ReadOnlyWorksheet
from openpyxl.worksheet.worksheet import Worksheet


class DataExtractor:
    def __init__(self):
        pass

    @staticmethod
    def get_worksheet(workbook: Workbook, sheet_index: int) -> Union[Worksheet, ReadOnlyWorksheet]:
        return workbook.worksheets[sheet_index]

    @staticmethod
    def get_workbook(file, read_only=True, data_only=True) -> Workbook:
        return openpyxl.load_workbook(file, read_only=read_only, data_only=data_only)

    @staticmethod
    def get_data_gen(
            worksheet: Union[Worksheet, ReadOnlyWorksheet],
            min_col: int, max_col: int, min_row: int, max_row: int = None, values_only=True
    ) -> Generator[Any, None, None]:
        return worksheet.iter_rows(
                min_row=min_row,
                max_row=max_row,
                min_col=min_col,
                max_col=max_col,
                values_only=values_only
        )

    @staticmethod
    def get_data(
            file, min_row=None, max_row=None, min_col=None, max_col=None, worksheet_index=None,
            read_only=True, data_only=True, values_only=True
    ) -> List[Any]:

        wb = DataExtractor.get_workbook(file, read_only=read_only, data_only=data_only)
        ws = DataExtractor.get_worksheet(wb, worksheet_index)
        data_gen = DataExtractor.get_data_gen(ws, min_row=min_row, max_row=max_row, min_col=min_col, max_col=max_col,
                                              values_only=values_only)
        if min_col is max_col:
            data = [val[0] for val in data_gen if val[0]]
        else:
            data = [vals for vals in data_gen if any(val for val in vals is not None)]
        return data

    @staticmethod
    def gen_files_from_dir(dir_path: str, file_types: Union[str, Tuple[str]] = None):
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
