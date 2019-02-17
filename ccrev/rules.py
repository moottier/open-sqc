from __future__ import annotations

import abc
from typing import List, TYPE_CHECKING, Union, Any, Dict, Type, Container

from ccrev.config import ST_DEV, MEAN

if TYPE_CHECKING:
    pass


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
        return all(datum > stats_data[MEAN] for datum in data)

    @staticmethod
    def is_positive(data: List[float], **stats_data) -> bool:
        return all(datum > stats_data[MEAN] for datum in data)


class Rule3(Rule):
    """
    increasing or decreasing trend

    positive trend is increasing
    """
    min_len_check = 6
    min_len_continuation_check = 2
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
    min_len_continuation_check = 2
    min_len_positivity_check = 2
    rule_number = 4

    @staticmethod
    def check(data: List[float], **stats_data) -> bool:
        return all(((a > b) - (a < b)) * ((b > c) - (b < c)) == -1 for a, b, c in zip(data, data[1:], data[2:]))

    @staticmethod
    def is_continued(data: List[float], signal_is_positive: bool, signal: Signal = None, **stats_data) -> bool:
        if signal_is_positive and len(signal) % 2 is 0:  # check if trend length is even with len(trend) % 2 is 0
            return data[0] > data[1]
        elif signal_is_positive and not len(signal) % 2 is 0:
            return data[0] < data[1]
        elif not signal_is_positive and len(signal) % 2 is 0:
            return data[0] < data[1]
        elif signal_is_positive and not len(data) % 2 is 0:
            return data[0] > data[1]

    @staticmethod
    def is_positive(data: List[float], **stats_data) -> bool:
        return data[0] < data[1]


class RuleChecker:
    def __init__(self, rules: Container[Type[Rule]]):
        self.rules = rules
        self._signals: List[Signal] = []

    def __getitem__(self, item):
        for rule in self.rules:
            if rule.rule_number is item:
                return rule

    def check(
            self,
            rule: Rule,
            data: List[float],
            return_type: Any = int,  # TODO fully implement
            **stats_data,
            #  return_type: Union[Type[int], Type[Signal], Type[Dict]]=int
    ) -> Union[List[Signal], List[int]]:  # -> Union[List[int], List[Signal], Dict[int, List[int]]]:
        """
        driver for rule-checking routine
        """

        signal: Signal = None
        for data_index, datum in enumerate(data):
            if any(data_index in signal for signal in self._signals):  # if signal already detected at data_index
                if signal:
                    self._signals.append(signal)
                    signal = None  # update signal list and clear signal if signal detected for data index
                continue  # skip data_index

            if signal:
                if rule.is_continued(
                        data[data_index:data_index + rule.min_len_continuation_check],
                        signal._is_positive,
                        signal  # TODO, why need pass signal._is_positive && signal??
                ):  # if data point continues signal
                    signal.end_index += 1
                else:
                    self._signals.append(signal)
                    signal = None  # stop signal and update signal list
                continue

            else:  # try to find new signal
                if len(data[data_index:data_index + rule.min_len_check]) is not rule.min_len_check:
                    continue  # don't check for signals near end of data set
                elif any(data_index in self._signals for
                         data_index in range(data_index, data_index + rule.min_len_check)):
                    continue  # don't check for signals if signal in remaining data
                else:
                    if rule.check(
                            data[data_index:data_index + rule.min_len_check],
                            **stats_data
                    ):
                        signal: Signal = Signal(rule.rule_number, data_index)
                        signal._is_positive = rule.is_positive(
                            data[data_index:data_index + rule.min_len_positivity_check]
                        )
                    continue

        signal: List[Signal] = self._signals
        self._signals = None  # reset RuleChecker state
        if isinstance(return_type, int):
            signal = self.convert_signal(signal, target_type=type(return_type))
        return signal

    def check_all_rules(self, data, return_type=int) -> Union[List[Signal], List[int]]:
        signals = []
        for rule in self.rules:
            signals.append(self.check(rule, data, return_type=Signal))
        signals = self._flatten_signals(signals)
        signals = self.convert_signal(signals, target_type=return_type)
        return signals

    @staticmethod
    def _flatten_signals(n_dim_signals: List[List[Signal]]) -> List[Signal]:
        signal_dim = len(n_dim_signals)
        if signal_dim is 0:
            return []
        if signal_dim is 1:
            return n_dim_signals[0]

        #  TODO Condense from here #
        signals: Dict = {}
        for signal_set_index, _ in enumerate(n_dim_signals):
            signal_id = n_dim_signals[signal_set_index][0].signal_id
            signals[signal_id] = n_dim_signals[signal_set_index]

        sorted_ids = sorted([signal_id for signal_id in signals.keys()])

        sorted_signals = []
        for signal_id in sorted_ids:
            sorted_signal_set = sorted(signals[signal_id], key=lambda signal: signal.start_index)
            sorted_signals.append(sorted_signal_set)
        #  TODO Condense to here #

        signals: List[List[Signal]] = sorted_signals
        # inner lists sorted by signal.start_index
        # outer list sorted by signal.signal_id

        # remove overlapping signals
        # signals with lower signal_id are kept over overlapped signals with higher signal_id
        for signal_set_index, signal_set in enumerate(signals):
            if signal_set_index is len(signals) - 1:
                break  # don't need to check if signals w/ greatest signal ID overlap anything
            for signal in signals[signal_set_index]:
                for higher_index in range(signal_set_index + 1, len(signals)):
                    for signal_from_higher_index in signals[higher_index]:
                        signal_indexes = (signal.start_index, signal.end_index)
                        if any(signal_index in signal_from_higher_index for signal_index in signal_indexes):
                            # remove signals that overlap signals with lower indexes
                            signals[higher_index].remove(signal_from_higher_index)
                        else:
                            continue

        signals: List[Signal] = sorted(
            [signal for signal_set in signals for signal in signal_set],
            key=lambda signal: signal.start_index
        )  # flatten & sort
        return signals

    @staticmethod
    def convert_signal(signal: Union[List[Signal], Signal], target_type=int):
        converted_signal = []
        if isinstance(target_type, int):
            for signal in signal:
                converted_signal.append(signal.signal_id)
        else:
            raise NotImplementedError
        return converted_signal
