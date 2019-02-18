from typing import Tuple
import os

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

#REVIEWER KWARGS
REV_DATA_COL = 'data_col'
REV_INDEX_COL = 'index_col'
REV_MIN_ROW = 'min_row'
REV_MAX_ROW = 'max_row'
REV_RULES = 'rules'
REV_ST_DEV = 'st_dev'
REV_MEAN = 'mean'