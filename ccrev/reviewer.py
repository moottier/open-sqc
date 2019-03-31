from datetime import datetime
from typing import List, Union, Any, Type

import matplotlib.ticker as mticker

from ccrev import config
from ccrev.charts.charting_base import ControlChart
from ccrev.extractor import DataExtractor
from ccrev.reporting import Report
from ccrev.rule_checking import RuleChecker


class Reviewer:
    DefaultReport: Type[Report] = Report

    def __init__(self, y_data_col=None, x_data_col=None, x_label_col=None,
                 min_row=None, max_row=None, rules=None, data_sheet_index=None,
                 load_stats_from_src=False, **stats_data_addresses):

        # works on equal length data cols starting & stopping at given min & max
        self.y_data_col = y_data_col
        self.x_data_col = x_data_col
        self.x_label_col = x_label_col
        self.data_min_row = min_row
        self.data_max_row = max_row
        self.data_sheet_index = data_sheet_index
        self.stats_data_addresses = stats_data_addresses

        self.report: Report = None
        self.data_extractor: DataExtractor = DataExtractor()
        self.rule_checker: RuleChecker = RuleChecker(rules=rules)

        self.config = {
            'try_to_load_stats_data': load_stats_from_src,
        }

        # List[List[title, ControlChart]]
        self.control_chart_data: List[List[Union[str, ControlChart]]] = []
        self._active_data = None

    @property
    def control_charts(self) -> List[ControlChart]:
        return [chart_item[1] for chart_item in self.control_chart_data]

    @property
    def chart_src_files(self) -> List[str]:
        return [chart_item[0] for chart_item in self.control_chart_data]

    @property
    def chart_titles(self):
        return [chart_item[1].title for chart_item in self.control_chart_data]

    def add_charts(self, src_dir: str, chart_type: Type[ControlChart]) -> None:
        for file in self.data_extractor.gen_files(src_dir):
            self.add_chart(file, chart_type)

    def load_data(self, chart_title: str) -> None:
        chart_index = self.chart_titles.index(chart_title)
        chart = self.control_charts[chart_index]

        # if len(gen_y_data) is not len(gen_x_data):
        #     # TODO log this? warn for this? print is okay for now
        #     #  but could improve...
        #     #  do this check elsewhere
        #     print('%s: data and data-index lengths mismatched' % src_file)

        chart.y_data = self._gen_y_data(chart_title)
        chart.x_data = self._gen_x_data(chart_title)
        chart.x_labels = self._gen_x_labels(chart_title)
        chart.stdev = self._gen_st_dev(chart_title) if \
            self.config['try_to_load_stats_data'] else None
        chart.mean = self._gen_mean(chart_title) if \
            self.config['try_to_load_stats_data'] else None

    def load_all_data(self) -> None:
        for chart_title, chart in zip(self.chart_titles, self.control_charts):
            self.load_data(chart_title)

    def add_chart(self, src_file: str, chart_type: Type[ControlChart],
                  title=None) -> None:
        if title in self.chart_titles:
            raise ValueError('Chart title cannot be a duplicate')

        # for all uses of title:
        # if not title then title <- DataExtractor.clean_file_names(src_file)
        chart = chart_type(
                y_data=None,
                title=title or self.data_extractor.clean_file_names(src_file)
        )

        self.data_extractor.add_workbook(src_file, title)
        self.control_chart_data.append([src_file, chart])

    def _gen_y_data(self, chart_title) -> List:
        reg = (
            self.data_min_row,
            self.data_max_row,
            self.y_data_col,
            self.y_data_col
        )
        yield from self.data_extractor.gen_items_in_region(
                chart_title,
                *reg,
                self.data_sheet_index
        )

    def _gen_x_data(self, chart_title) -> List:
        reg = (
            self.data_min_row,
            self.data_max_row,
            self.x_data_col,
            self.x_data_col
        )
        yield from self.data_extractor.gen_items_in_region(
                chart_title,
                *reg,
                self.data_sheet_index
        )

    def _gen_x_labels(self, chart_title) -> List:
        reg = (
            self.data_min_row,
            self.data_max_row,
            self.x_label_col,
            self.x_label_col
        )
        yield from self.data_extractor.gen_items_in_region(
                chart_title,
                *reg,
                self.data_sheet_index
        )

    def _gen_st_dev(self, chart_title) -> List:
        reg = (
            self.stats_data_addresses[config.STDEV][0],
            self.stats_data_addresses[config.STDEV][0],
            self.stats_data_addresses[config.STDEV][1],
            self.stats_data_addresses[config.STDEV][1]
        )
        yield from self.data_extractor.gen_items_in_region(
                chart_title,
                *reg,
                self.data_sheet_index
        )

    def _gen_mean(self, chart_title) -> List:
        reg = (
            self.stats_data_addresses[config.MEAN][0],
            self.stats_data_addresses[config.MEAN][0],
            self.stats_data_addresses[config.MEAN][1],
            self.stats_data_addresses[config.MEAN][1]
        )
        yield from self.data_extractor.gen_items_in_region(
                chart_title,
                *reg,
                self.data_sheet_index
        )

    def check_all_rules(self):
        for chart in self.control_charts:
            if not chart.plotted_x_data:
                print(
                        f'Trying to check chart without loading data: '
                        f'{chart.title}'
                )
                continue

            chart.signals = self.rule_checker.check_all_rules(
                    chart.plotted_y_data,
                    st_dev=chart.stdev,
                    mean=chart.mean
            )

    def build_report(self, report_name=None, save=True):
        self.report = Reviewer.DefaultReport()
        for chart in self.control_charts:
            self.report.add_chart(chart, signal_labels=chart.x_labels)
        self.report.name = report_name

        if save:
            self.save_report()

    def save_report(self):
        self.report.save()

    def swap_chart_order(self, pos1, pos2) -> None:
        self.control_chart_data[pos2], self.control_chart_data[pos1] = \
            self.control_chart_data[pos1], self.control_chart_data[pos2]

    def move_chart_up(self, pos) -> None:
        Reviewer._can_move(pos, pos - 1) and self.swap_chart_order(pos, pos - 1)

    def move_chart_down(self, pos) -> None:
        Reviewer._can_move(pos, pos + 1) and self.swap_chart_order(pos, pos + 1)

    @staticmethod
    def _can_move(pos1, pos2) -> bool:
        args = [pos1, pos2]
        if any(arg < 0 for arg in args):
            raise IndexError('list index out of range')
        return True

    def overwrite_mean(self, chart_title, mean):
        chart_idx = self.chart_titles.index(chart_title)
        self.control_charts[chart_idx].mean = mean

    def overwrite_stdev(self, chart_title, stdev):
        chart_idx = self.chart_titles.index(chart_title)
        self.control_charts[chart_idx].stdev = stdev

    def resize_chart_axes(self, chart_title, x_min, x_max, y_min, y_max):
        chart_idx = self.chart_titles.index(chart_title)
        self.control_charts[chart_idx].plot.resize_plot_axes(
                x_min,
                x_max,
                y_min,
                y_max
        )

    def set_data_start_by_idx(self, chart_title: str, idx: Any):
        chart_idx = self.chart_titles.index(chart_title)
        chart = self.control_charts[chart_idx]
        chart.start_idx = idx

    def set_data_start_date(self, chart_title, dt: datetime):
        chart_idx = self.chart_titles.index(chart_title)
        chart = self.control_charts[chart_idx]
        chart.data_start = dt

    def set_data_end_date(self, chart_title, dt: datetime):
        chart_idx = self.chart_titles.index(chart_title)
        chart = self.control_charts[chart_idx]
        chart.data_end = dt
