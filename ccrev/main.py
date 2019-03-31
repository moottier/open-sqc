from __future__ import annotations

import datetime

from ccrev import config
# TODO: Move to config file
from ccrev.charts.charts import IChart
from ccrev.config import TEST_DIR
from ccrev.reviewer import Reviewer

if __name__ == '__main__':
    reviewer = Reviewer(**config.REVIEWER_KWARGS)

    # test dir
    reviewer.add_charts(
        TEST_DIR,
        IChart
    )

    # REMOVE THESE BECAUSE THEY SHOULD BE MR CHARTS
    remove = ('CO2 by CarboQC', 'SO2 by Mettler')
    for index, title in enumerate(reviewer.chart_titles):
        if any(rem in title for rem in remove):
            del reviewer.control_charts[index]

    # TODO separate DataExtractor from reviewer
    #  want to be able to extract data
    #  do some cleaning
    #  then put it in a report
    reviewer.load_all_data()
    reviewer.check_all_rules()

    # for chart in reviewer.control_charts:
    #     reviewer.label_x_axis(chart.title)

    # TODO
    #  want an interface like:
    #  reviewer.label_x_axis(chart=chart.title, labels=DataExtractor.x_labels)
    #  reviewer.label_signals(chart=chart.title, labels=DataExtractor.signal_labels)
    #  reviewer.set_data_start(chart=chart.title, key='03/23/2019')
    #  reviewer.set_data_end(chart=chart.title, key='03/29/2019')

    reviewer.build_report(report_name=datetime.datetime.today(), save=True)
