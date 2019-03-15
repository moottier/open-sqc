from __future__ import annotations

import datetime

from ccrev import config
# TODO: Move to config file
from ccrev.charts.charts import IChart
from ccrev.data_processing import Reviewer

if __name__ == '__main__':
    reviewer = Reviewer(**config.REVIEWER_KWARGS)

    # main dir
    reviewer.add_control_charts_from_directory(
        r'F:\LabData\Lab\ISO 17025\Development\Control Chart',
        IChart
    )
    # Y15 dir
    reviewer.add_control_charts_from_directory(
        r'F:\LabData\Lab\ISO 17025\Development\Control Chart\Y15 Control Charts',
        IChart
    )
    # HPLC dir
    reviewer.add_control_charts_from_directory(
        r'F:\LabData\Lab\ISO 17025\Development\Control Chart\HPLC Control Charts',
        IChart
    )
    # metals dir
    reviewer.add_control_charts_from_directory(
        r'F:\LabData\Lab\ISO 17025\Development\Control Chart\Metals by ICP-OES Control Charts',
        IChart
    )

    # REMOVE THESE BECAUSE THEY SHOULD BE MR CHARTS
    remove = ('CO2 by CarboQC.xlsx', 'SO2 by Mettler.xlsx')
    for index, src in enumerate(reviewer.source_files):
        if any(rem in src for rem in remove):
            del reviewer.control_charts[index]

    reviewer.check_all_rules()

    reviewer.build_report(report_name=datetime.datetime.today(), save=True)
