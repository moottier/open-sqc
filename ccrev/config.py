import os
from typing import Tuple

from ccrev.charts.charts import IChart
from ccrev.rules import Rule1, Rule2, Rule3, Rule4

# friendly identifiers for stats data
STDEV = 'STDEV'
MEAN = 'MEAN'

# file paths
TEST_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test'))
PATH: str = os.getcwd()
TEST_PATH: str = os.path.join(os.getcwd(), 'test')

DATA_COL: int = 4  # 1 indexed
DATETIME_COL: int = 6
TIME_COL: int = 2
DATE_COL: int = 1
INDEX_COL: int = 6
DATA_SHEET: int = 0  # 0 indexed
DATA_START_ROW: int = 2  # 1 indexed
WS_MEAN_ADDR: Tuple[int, int] = (2, 15)  # row, col
WS_STDEV_ADDR: Tuple[int, int] = (2, 16)  # row, col
EXCEL_FILE_EXTENSIONS = ('.xlsx', '.xlsm', '.xltx', '.xltm')
CSV_FILE_EXTENSIONS = ('.csv',)
IGNORE_FILES = ('~$',)
EXCLUDE_CELL_VALUES = (None, '#REF!')

# for testing
REVIEWER_KWARGS = {
    'y_data_col'                   : DATA_COL,
    'x_label_col'                  : DATETIME_COL,
    'min_row'                      : DATA_START_ROW,
    'max_row'                      : None,
    'rules'                        : (Rule1, Rule2, Rule3, Rule4),
    STDEV                          : WS_STDEV_ADDR,
    MEAN                           : WS_MEAN_ADDR,
    'load_stats_from_src'          : True,
    'data_sheet_index'             : DATA_SHEET,
    'map_signals_to_provided_index': False,
    'plot_against_provided_index'  : False,
    'signal_dates_short_format'    : True,
    'index_dates_short_format'     : True,
}

# PLOT CONFIG
ORANGE = '#FF8C00'

# EXPECTED CHART FORMATS
MR_CHART_FORMAT = {
    'data_worksheet': DATA_SHEET,
    'date_col'      : 1,
    'time_col'      : 2,
    'data_col'      : 4,
    'datetime_col'  : 5,
    'mean_cell'     : (2, 12),
    'st_dev_cell'   : (2, 13),
    'exclude_vals'  : EXCLUDE_CELL_VALUES,
    'min_row_cols'  : 2,
    'max_row_cols'  : None
}

I_CHART_FORMAT = {
    'data_worksheet': DATA_SHEET,
    'date_col'      : 1,
    'time_col'      : 2,
    'data_col'      : 4,
    'datetime_col'  : 6,
    'mean_cell'     : (2, 15),
    'st_dev_cell'   : (2, 16),
    'exclude_vals'  : EXCLUDE_CELL_VALUES,
    'min_row_cols'  : 2,
    'max_row_cols'  : None
}
CHART_TYPES = {'I-Chart': IChart, 'MR-Chart': IChart, }  # TODO update when MRChart done
