from __future__ import annotations

import datetime
import statistics
from typing import Dict, List, Type

from ccrev import config
# TODO: Move to config file
from ccrev.charts.chart_base import ControlChart
from ccrev.data_processor import DataExtractor
from ccrev.reports import Report
from ccrev.rules import RuleChecker, Rule1, Rule2, Rule3, Rule4

REVIEWER_CONFIG = {
    config.REV_DATA_COL : config.DATA_COL,
    config.REV_INDEX_COL: config.INDEX_COL,
    config.REV_MIN_ROW: config.DATA_START_ROW,
    config.REV_MAX_ROW: None,
    config.REV_RULES: (Rule1, Rule2, Rule3, Rule4),
    config.REV_ST_DEV: config.WS_STDEV_ADDR,
    config.REV_MEAN: config.WS_MEAN_ADDR
}


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
                    data=data_set[index], signals=signals, chart_type=self.chart_type, stats_data=self.get_stats_data()
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


if __name__ == '__main__':
    reviewer = Reviewer(REVIEWER_CONFIG)
    reviewer.review(config.WORKING_DIR)
    reviewer.build_report(report_name=datetime.datetime.today(), save=True)
