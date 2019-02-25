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
from ccrev.config import EXCEL_FILE_EXTENSIONS
from ccrev.reporting import Report
from ccrev.rule_checking import RuleChecker


class DataExtractor:
    def __init__(self):
        pass

    @staticmethod
    def get_excel_data(
            src_file, min_row=None, max_row=None, min_col=None, max_col=None, worksheet_index=None,
            read_only=True, data_only=True, values_only=True
    ) -> List[Any]:

        wb = DataExtractor.load_workbook(
                src_file,
                read_only=read_only,
                data_only=data_only
        )
        ws = DataExtractor.load_worksheet(
                wb,
                worksheet_index
        )
        data_iter = DataExtractor._get_data_iter(
                ws,
                min_row=min_row,
                max_row=max_row,
                min_col=min_col,
                max_col=max_col,
                values_only=values_only
        )

        if min_col is max_col and min_row is max_row:
            # data from single cell
            data = [val[0] for val in data_iter if val[0]][0]
        elif min_col is max_col:
            # data from single column
            data = [val[0] for val in data_iter if val[0]]
        else:
            # data from contiguous columns
            data = [vals for vals in data_iter if any(val for val in vals is not None)]
        return data

    @staticmethod
    def gen_files(src_dir: str, file_types: Union[str, Tuple[str]] = None):
        for file in os.listdir(src_dir):
            file_in_dir = join(src_dir, file)
            if file_types and file.endswith(file_types):
                yield file_in_dir
            elif not file_types:
                yield file
            else:
                continue

    @staticmethod
    def load_workbook(file, read_only=True, data_only=True) -> Workbook:
        return openpyxl.load_workbook(file, read_only=read_only, data_only=data_only)

    @staticmethod
    def load_worksheet(workbook: Workbook, sheet_index: int) -> Union[Worksheet, ReadOnlyWorksheet]:
        return workbook.worksheets[sheet_index]

    @staticmethod
    def _get_data_iter(
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
        self.data_extractor: DataExtractor = DataExtractor()
        self.rule_checker: RuleChecker = RuleChecker(rules=rules)

        # uses filenames as keys
        # values are list of data, list of data index, stats data, control chart type
        self.data: Dict[str, List[List[float], List[Any], Dict[str, float], Type[ControlChart]]] = {}
        self._active_data = None

    @staticmethod
    def _data_factory(data: List[float], data_index=None, stats_values=None, control_chart:Type[ControlChart]=None) -> List:
        return [data, data_index, stats_values, control_chart]

    def control_chart_factory(self, data, signals, chart_type: Type[ControlChart], **stats_data) -> ControlChart:
        return self.chart_type(
                data=data,
                signals=signals,
                chart_type=chart_type,
                stats_data=stats_data
        )

    def check_all_rules(self, data_source):
        data, data_index = self.get_data(data_source)
        if isinstance(data[0], List):
            for index, data_set in enumerate(data_source):
                self._active_data = data_set[index]
                signals = self.rule_checker.check_all_rules(self._active_data)
                chart = self.control_chart_factory(
                        data=data_set[index], signals=signals, chart_type=self.chart_type,
                        stats_data=self.get_stats_data()
                )
                self.data.append(chart)
                self._active_data = None
        else:
            self._active_data = data
            signals = self.rule_checker.check_all_rules(self._active_data)
            chart = self.control_chart_factory(
                    data=data, signals=signals, chart_type=self.chart_type, stats_data=self.get_stats_data()
            )
            self.data.append(chart)
        self._active_data = None

    def get_data(self, src_file: str) -> Tuple[List[float], List]:
        if not src_file.endswith(EXCEL_FILE_EXTENSIONS):
            # TODO handle CSVs
            raise NotImplementedError

        data = self.data_extractor.get_excel_data(
                src_file,
                min_col=self.data_col,
                max_col=self.data_col,
                min_row=self.min_row,
                max_row=self.max_row,
                worksheet_index=self.data_sheet_index
        )
        data_index = self.data_extractor.get_excel_data(
                src_file,
                min_col=self.index_col,
                max_col=self.index_col,
                min_row=self.min_row,
                max_row=self.max_row,
                worksheet_index=self.data_sheet_index
        )
        return data, data_index

    def add_data(self, src_file: str):
        data, data_index = self.get_data(src_file)
        self.data[src_file] = Reviewer._data_factory(data, data_index, )


    def get_stats_data(self) -> Dict:
        st_dev = self.data_extractor.get_excel_data(
                address=self.stats_data_addresses[config.ST_DEV], worksheet_index=self.data_sheet_index
        ) if self.stats_data_addresses[config.ST_DEV] else statistics.stdev(self._active_data)

        mean = self.data_extractor.get_excel_data(
                address=self.stats_data_addresses[config.MEAN]
        ) if self.stats_data_addresses[config.MEAN] else statistics.mean(self._active_data)

        return {config.ST_DEV: st_dev, config.MEAN: mean}

    def build_report(self, report_name=None, save=True):
        self.report = Reviewer.DefaultReport()
        for reviewed_chart in self.data:
            self.report.add_chart(reviewed_chart)
        self.report.name = report_name

        if save:
            self.save_report()

    def save_report(self):
        self.report.save()
