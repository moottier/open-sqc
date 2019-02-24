from __future__ import annotations

import datetime

from ccrev import config
# TODO: Move to config file
from ccrev.data_processing import Reviewer

if __name__ == '__main__':
    reviewer = Reviewer(config.REVIEWER_KWARGS)
    reviewer.review(config.WORKING_DIR)
    reviewer.build_report(report_name=datetime.datetime.today(), save=True)
