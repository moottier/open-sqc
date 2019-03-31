import os
import re
from typing import Union, List, Any, Tuple, Dict

import openpyxl
from openpyxl import Workbook

from ccrev import config


def _gen_stop_at(stop):
    def decorator(gen):
        def wrapper(*args):
            for val in gen(*args):
                if val[0] == stop:
                    break
                else:
                    yield val[0]
        return wrapper
    return decorator


class DataExtractor:
    def __init__(self):
        self.workbooks: Dict[str, Workbook] = {}

    def add_workbook(self, src_file, title: str = None) -> Workbook:
        return self.workbooks.setdefault(
                title or self.clean_file_names(src_file),
                openpyxl.load_workbook(src_file, read_only=True, data_only=True)
        )

    def get_region_iter(
            self, title, min_row, max_row,
            min_col, max_col, sheet_index, values_only=True
    ):
        reg = min_row, max_row, min_col, max_col
        ws = self.workbooks[title].worksheets[sheet_index]
        return ws.iter_rows(*reg, values_only)

    @_gen_stop_at(None)
    def gen_items_in_region(
            self, title, min_row, max_row, min_col,
            max_col, sheet_index, values_only=True
    ):
        reg = min_row, max_row, min_col, max_col
        yield from self.get_region_iter(title, *reg, sheet_index, values_only)

    @staticmethod
    def gen_files(
            src_dir: str,
            includes: Union[str, Tuple[str]] = config.EXCEL_FILE_EXTENSIONS,
            excludes: Tuple[str] = config.IGNORE_FILES
    ) -> str:
        for file in os.listdir(src_dir):
            file = os.path.join(src_dir, file)
            if includes and not file.endswith(includes):
                continue
            if excludes and any(exclude in file for exclude in excludes):
                continue
            else:
                yield file

    @staticmethod
    def remove_file_extensions(s: str) -> str:
        return re.sub(r'\..+$', '', s)

    @staticmethod
    def clean_file_names(src_file):
        src_file = os.path.basename(src_file)
        src_file = DataExtractor.remove_file_extensions(src_file)
        return src_file
