from __future__ import annotations

import abc
from typing import List

# TODO should be declared elsewhere

ST_DEV, MEAN = 'stdev', 'mean'


class Rule:
    """
    used to check for data patterns (trends) specified by .check and min duration
    rule_number should be identifying
    """
    min_len_check: int = None
    min_len_continuation_check: int = None
    min_len_positivity_check: int = None
    rule_number: int = None

    @staticmethod
    @abc.abstractmethod
    def check(data: List[float], **stats_data) -> bool:
        """
        return true if specified pattern exists in param nums
        TODO stdev & mean should be KWARGS, not every child class uses/needs
        """
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def is_continued(data: List[float], signal_is_positive: bool, signal: Signal = None, **stats_data) -> bool:
        """
        returns true if pattern represented by trend is continued by data at data index
        """
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def is_positive(data: List[float], **stats_data) -> bool:
        """
        used to distinguish symmetrical trends
        (i.e. increasing trend vs. decreasing trend, run above mean vs. run below mean)

        returns true for "positive" trends

        positive/negative classification is semi-arbitrary certain trends (i.e. alternating increasing/decreasing)
        """
        raise NotImplementedError


class Rule1(Rule):
    """
    point past action limit
    """

    min_len_check: int = 1
    min_len_continuation_check: int = None
    min_len_positivity_check: int = 1
    rule_number: int = 1

    @staticmethod
    def check(data: List[float], **stats_data) -> bool:
        return not (stats_data[MEAN] - 3 * stats_data[ST_DEV]) < data[0] < (stats_data[MEAN] + 3 * stats_data[ST_DEV])

    @staticmethod
    def is_continued(data: List[float], signal_is_positive: bool, signal: Signal = None, **stats_data) -> bool:
        return False

    @staticmethod
    def is_positive(data: List[float], **stats_data) -> bool:
        return all(datum > stats_data[MEAN] for datum in data)


class Rule2(Rule):
    """
    run above or below the mean
    """
    min_len_check = 8
    min_len_continuation_check = 1
    min_len_positivity_check = 1
    rule_number = 2

    @staticmethod
    def check(data: List[float], **stats_data) -> bool:
        return all(datum > stats_data[MEAN] for datum in data) or all(datum < stats_data[MEAN] for datum in data)

    @staticmethod
    def is_continued(data: List[float], signal_is_positive: bool, signal: Signal = None, **stats_data) -> bool:
        return signal._is_positive and all(datum > stats_data[MEAN] for datum in data) or \
               not signal._is_positive and all(datum < stats_data[MEAN] for datum in data)

    @staticmethod
    def is_positive(data: List[float], **stats_data) -> bool:
        return all(datum > stats_data[MEAN] for datum in data)


class Rule3(Rule):
    """
    increasing or decreasing trend

    positive trend is increasing
    """
    min_len_check = 6
    min_len_continuation_check = 1
    min_len_positivity_check = 2
    rule_number = 3

    @staticmethod
    def check(data: List[float], **stats_data) -> bool:
        return all(a < b for a, b in zip(data, data[1:])) \
               or all(a > b for a, b in zip(data, data[1:]))

    @staticmethod
    def is_continued(data: List[float], signal_is_positive: bool, signal: Signal = None, **stats_data) -> bool:
        if signal_is_positive:
            return data[1] > data[0]
        else:
            return data[1] < data[0]

    @staticmethod
    def is_positive(data: List[float], **stats_data) -> bool:
        return data[0] < data[len(data) - 1]


class Rule4(Rule):
    """
    excessive oscillation

    positive trends start increasing->decreasing
    """
    min_len_check = 14
    min_len_continuation_check = 1
    min_len_positivity_check = 2
    rule_number = 4

    @staticmethod
    def check(data: List[float], **stats_data) -> bool:
        return all(((a > b) - (a < b)) * ((b > c) - (b < c)) == -1 for a, b, c in zip(data, data[1:], data[2:]))

    @staticmethod
    def is_continued(data: List[float], signal_is_positive: bool, signal: Signal = None, **stats_data) -> bool:
        signal_len_is_odd = len(signal) % 2
        if signal_is_positive and signal_len_is_odd:  # check if trend length is even with len(trend) % 2 is 0
            return data[0] < data[1]
        elif signal_is_positive and not signal_len_is_odd:
            return data[0] > data[1]
        elif not signal_is_positive and signal_len_is_odd:
            return data[0] > data[1]
        elif signal_is_positive and not signal_len_is_odd:
            return data[0] < data[1]

    @staticmethod
    def is_positive(data: List[float], **stats_data) -> bool:
        return data[0] < data[1]


class Signal:
    def __init__(self, signal_id: int, start_index: int, end_index: int = None):
        self.signal_id: int = signal_id  # identify rule associated w/ signal
        self.start_index: int = start_index
        self.end_index: int = end_index if end_index else start_index + 1

        self._is_positive = None

    def __contains__(self, data_index):
        return data_index in range(self.start_index, self.end_index)

    def __len__(self):
        return self.end_index - self.start_index