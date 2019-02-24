import os
import statistics
from os.path import join
from typing import List, Tuple, Union, Any, Generator, Type, Dict

import openpyxl
import openpyxl.cell
import openpyxl.utils.exceptions
from openpyxl.workbook import Workbook
from openpyxl.worksheet._read_only import ReadOnlyWorksheet
from openpyxl.worksheet.worksheet import Worksheet

from ccrev import config
from ccrev.charts.chart_base import ControlChart
from ccrev.reporting import Report
from ccrev.rule_checking import RuleChecker


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

        if min_col is max_col and min_row is max_row:
            data = [val[0] for val in data_gen if val[0]][0]
        elif min_col is max_col:
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
class Reviewer:
    DefaultReport: Type[Report] = Report

    def __init__(self, data_col=None, index_col=None, min_row=None, max_row=None, chart_type=None, rules=None,
                 data_sheet_index=None, report_type=None, **stats_data_addresses):
        self.data_col = data_col
        self.index_col = index_col
        self.min_row = min_row
        self.max_row = max_row
        self.stats_data_addresses = stats_data_addresses
        self.data_sheet_index = data_sheet_index
        self.chart_type: Type[ControlChart] = chart_type

        self.report: Report = report_type if report_type else Reviewer.DefaultReport
        self.extractor: DataExtractor = DataExtractor()
        self.rule_checker: RuleChecker = RuleChecker(rules=rules)

        self.reviewed_data = []
        self._active_data = None

    def make_control_chart(self, data, signals, chart_type: Type[ControlChart], **stats_data) -> ControlChart:
        return self.chart_type(
                data=data,
                signals=signals,
                chart_type=chart_type,
                stats_data=stats_data
        )

    def review(self, data_source):
        data, data_index = self.get_data(data_source)
        if isinstance(data[0], List):
            for index, data_set in enumerate(data_source):
                self._active_data = data_set[index]
                signals = self.rule_checker.check_all_rules(self._active_data)
                chart = self.make_control_chart(
                        data=data_set[index], signals=signals, chart_type=self.chart_type,
                        stats_data=self.get_stats_data()
                )
                self.reviewed_data.append(chart)
                self._active_data = None
        else:
            self._active_data = data
            signals = self.rule_checker.check_all_rules(self._active_data)
            chart = self.make_control_chart(
                    data=data, signals=signals, chart_type=self.chart_type, stats_data=self.get_stats_data()
            )
            self.reviewed_data.append(chart)
        self._active_data = None

    def get_data(self, data_source):
        data = self.extractor.get_data(
                data_source,
                col=self.data_col,
                min_row=self.min_row,
                worksheet_index=self.data_sheet_index
        )
        data_index = self.extractor.get_data(
                data_source,
                col=self.index_col,
                min_row=self.min_row,
                worksheet_index=self.data_sheet_index
        )
        return data, data_index

    def get_stats_data(self) -> Dict:
        st_dev = self.extractor.get_data(
                address=self.stats_data_addresses[config.ST_DEV], worksheet_index=self.data_sheet_index
        ) if self.stats_data_addresses[config.ST_DEV] else statistics.stdev(self._active_data)

        mean = self.extractor.get_data(
                address=self.stats_data_addresses[config.MEAN]
        ) if self.stats_data_addresses[config.MEAN] else statistics.mean(self._active_data)

        return {config.ST_DEV: st_dev, config.MEAN: mean}

    def build_report(self, report_name=None, save=True):
        self.report = Reviewer.DefaultReport()
        for reviewed_chart in self.reviewed_data:
            self.report.add_chart(reviewed_chart)
        self.report.name = report_name

        if save:
            self.save_report()

    def save_report(self):
        self.report.save()