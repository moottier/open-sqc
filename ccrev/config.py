from typing import Tuple
import os

from ccrev.rules import Rule1, Rule2, Rule3, Rule4

PLOT_CENTER = 'center'
PLOT_UAL = 'ual'
PLOT_LAL = 'lal'
PLOT_UWL = 'uwl'
PLOT_LWL = 'lwl'
PLOT_DATA = 'data'
ST_DEV = 'st_dev'
MEAN = 'mean'
WORKING_DIR = r'H:\code\ccrev\ccrev\output'
PATH: str = os.getcwd()
TEST_PATH: str = os.path.join(os.getcwd(), 'test')
DATA_COL: int = 4  # 1 indexed
INDEX_COL: int = 6
DATA_SHEET: int = 0  # 0 indexed
DATA_START_ROW: int = 2  # 1 indexed
WS_MEAN_ADDR: Tuple[int, int] = (2, 15)
WS_STDEV_ADDR: Tuple[int, int] = (2, 16)
EXCEL_FILE_EXTENSIONS = ('.xlsx', '.xlsm', '.xltx', '.xltm')
CSV_FILE_EXTENSIONS = ('.csv',)

REVIEWER_KWARGS = {
    'data_col' : DATA_COL,
    'index_col': INDEX_COL,
    'min_row'  : DATA_START_ROW,
    'max_row'  : None,
    'rules'    : (Rule1, Rule2, Rule3, Rule4),
    'st_dev'   : WS_STDEV_ADDR,
    'mean'     : WS_MEAN_ADDR
}