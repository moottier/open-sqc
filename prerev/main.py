import datetime
import math
import os
import statistics
import sys
from dataclasses import dataclass
from typing import Tuple, Union, Generator, Any

import openpyxl
import openpyxl.cell

from ccrev import config


@dataclass(eq=False)
class ControlChartTemplate:
    excel_source: str
    data_worksheet: int
    date_col: int
    time_col: int
    data_col: int
    datetime_col: int
    mean_cell: Tuple[int, int]
    st_dev_cell: Tuple[int, int]

    exclude_vals: Tuple

    min_row_cols: Union[int, None] = None
    max_row_cols: Union[int, None] = None

    def __post_init__(self):
        ws = openpyxl.load_workbook(file, read_only=True, data_only=True).worksheets[self.data_worksheet]
        dates: Generator = self.get_row_iter(
            ws,
            min_row=self.min_row_cols, min_col=self.date_col, max_col=self.date_col,
            values_only=False
        )
        times: Generator = self.get_row_iter(
            ws,
            min_row=self.min_row_cols, min_col=self.time_col, max_col=self.time_col,
            values_only=False
        )
        data: Generator = self.get_row_iter(
            ws,
            min_row=self.min_row_cols, min_col=self.data_col, max_col=self.data_col,
            values_only=False
        )
        datetimes: Generator = self.get_row_iter(
            ws,
            min_row=self.min_row_cols, min_col=self.datetime_col,
            max_col=self.datetime_col, values_only=False
        )
        mean: Generator = self.get_row_iter(
            ws,
            min_row=self.mean_cell[0], max_row=self.mean_cell[0],
            min_col=self.mean_cell[1], max_col=self.mean_cell[1],
            values_only=False
        )
        stdev: Generator = self.get_row_iter(
            ws,
            min_row=self.st_dev_cell[0], max_row=self.st_dev_cell[0],
            min_col=self.st_dev_cell[1], max_col=self.st_dev_cell[1],
            values_only=False
        )

        self.validate(dates, expected_types=(datetime.datetime,))
        self.validate(times, expected_types=(int,))
        self.validate(data, expected_types=(float, int))
        self.validate(datetimes, expected_types=(datetime.datetime,))

        data_iter = self.get_row_iter(
            ws,
            min_row=self.min_row_cols, min_col=self.data_col, max_col=self.data_col,
            values_only=False
        )
        expected_mean = statistics.mean(list(cell.value for row in data_iter for cell in row))
        data_iter = self.get_row_iter(
            ws,
            min_row=self.min_row_cols, min_col=self.data_col, max_col=self.data_col,
            values_only=False
        )
        expected_st_dev = statistics.stdev(list(cell.value for row in data_iter for cell in row))

        self.validate(mean, expected_types=(int, float), approx_values_expected=(expected_mean,))
        self.validate(stdev, expected_types=(int,), approx_values_expected=(expected_st_dev,))

    def validate(self,
                 row_iter: Generator[Tuple[openpyxl.cell.Cell], None, None],
                 expected_types: Tuple = None,
                 exact_values_expected: Tuple[Any] = None,
                 approx_values_expected: Tuple[Any] = None) -> None:

        for row in row_iter:
            for cell in row:
                cell: openpyxl.cell.Cell
                cell_val = cell.value
                if cell_val in self.exclude_vals:
                    raise ExcelValueError(self.excel_source, cell, )
                if expected_types and not isinstance(cell_val, expected_types):
                    raise ExcelValueError
                if exact_values_expected and cell_val not in exact_values_expected:
                    raise ExcelValueError
                if approx_values_expected and not \
                        any(math.isclose(cell_val, val, rel_tol=0.2) for val in approx_values_expected):
                    raise ExcelValueError

    @staticmethod
    def get_row_iter(ws, min_row, min_col, max_col, values_only, max_row=None):
        return ws.iter_rows(min_row, max_row, min_col, max_col, values_only)


class ExcelValueError(ValueError):
    MSGS = ('excluded value found', 'unexpected type found', 'value too far for expected value')

    def __init__(self, excel_file_name, cell: openpyxl.cell.Cell, msg: str = None):
        self.excel_file_name = excel_file_name
        self.cell = cell
        self.msg = msg + 'in %s at $%s%s' % (self.excel_file_name, cell.column_letter, cell.row)


if __name__ == '__main__':
    src = sys.argv[1]

    mr_charts = ('CO2', 'SO2')

    control_charts = []

    files = filter(lambda f: any(ext in f for ext in config.EXCEL_FILE_EXTENSIONS), os.listdir(src))
    for file in files:
        file = os.path.join(src, file)
        try:
            if any(mr_chart in file for mr_chart in mr_charts):
                control_charts.append(
                    ControlChartTemplate(
                        excel_source=file,
                        **config.MR_CHART_FORMAT
                    )
                )
            else:
                control_charts.append(
                    ControlChartTemplate(
                        excel_source=file,
                        **config.I_CHART_FORMAT
                    )
                )
        except ExcelValueError as e:
            print(e.msg)
            continue
