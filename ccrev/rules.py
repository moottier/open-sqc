from __future__ import annotations

import abc
import copy
import itertools
from typing import List, TYPE_CHECKING, Union, Any, Dict, Type, Sequence

#from ccrev.config import ST_DEV, MEAN

if TYPE_CHECKING:
    import ccrev.config

#TODO should be declared elsewhere
ST_DEV, MEAN = 'stdev', 'mean'


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


# TODO return all signals as List[int]
class RuleChecker:
    def __init__(self, rules: Sequence[Type[Rule]]):
        self.rules = rules
        self._signals: List[Signal] = []

    def __getitem__(self, item):
        for rule in self.rules:
            if rule.rule_number is item:
                return rule

    def check(
            self,
            rule: Type[Rule],
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
            print('')
            if self._signals and any(data_index in signal for signal in self._signals):  # if signal already detected at data_index
                if signal:
                    self._signals.append(signal)
                    signal = None  # update signal list and clear signal if signal detected for data index
                continue  # skip data_index

            if signal:
                min_len_continuation_check = rule.min_len_continuation_check or 0
                if rule.is_continued(
                        #data[data_index:data_index + min_len_continuation_check],
                        data[data_index-min_len_continuation_check:data_index+1],
                        signal._is_positive,
                        signal,
                        **stats_data# TODO, why need pass signal._is_positive && signal??
                ):  # if data point continues signal
                    signal.end_index += 1
                else:
                    self._signals.append(signal)
                    signal = None  # stop signal and update signal list

            if not signal:  # try to find new signal
                if len(data[data_index:data_index + rule.min_len_check]) is not rule.min_len_check:
                    continue  # don't check for signals near end of data set
                elif self._signals and any(data_index in self._signals for
                         data_index in range(data_index, data_index + rule.min_len_check)):
                    continue  # don't check for signals if signal in remaining data
                else:
                    if rule.check(
                            data[data_index:data_index + rule.min_len_check],
                            **stats_data
                    ):
                        signal: Signal = Signal(rule.rule_number, data_index)
                        signal._is_positive = rule.is_positive(
                                data[data_index:data_index + rule.min_len_positivity_check], **stats_data
                        )
                    continue
        signal and self._signals.append(signal)  # for signal that goes to end of dataset append to signals
        signal: List[Signal] = self._signals
        self._signals = []  # reset RuleChecker state
        if isinstance(return_type, int):
            signal = self._signals_to_ints(signal, len(data))
        return signal

    # TODO get rid of this 'return_type' stuff it's wonky
    def check_all_rules(self, data, return_type=int, **stats_data) -> List[int]:
        signals = []
        for index, rule in enumerate(self.rules, 1):
            found_signals = self.check(rule, data, return_type=Signal, **stats_data)
            signals.append(found_signals)

        signals = self._flatten_signals(signals)
        signals = self._remove_overlaps(signals)
        signals = self._signals_to_ints(signals, len(data))
        return signals

    @staticmethod
    def _flatten_signals(signals: List[List[Signal]]) -> List[Signal]:
        signals = itertools.chain(*signals)
        return list(signals)

    def _remove_overlaps(self, signals: List[Signal]) -> List[Signal]:
        signals_to_remove = []
        for signal_index, signal in enumerate(signals):
            remaining_signals = signals[signal_index+1:]
            for remaining_signal in remaining_signals:
                trim_end = signal.end_index - 1 in remaining_signal
                trim_front = signal.start_index in remaining_signal
                split = trim_end and trim_front
                #TODO wrap up this three if blocks into a function that takes care of all the repeating code
                if signal.end_index - 1 in remaining_signal and signal.start_index in remaining_signal:  # split
                    signal_min_len = [  # TODO need better way to check if signal can be shortened
                        rule for rule in self.rules if rule.rule_number is remaining_signal.signal_id
                    ][0].min_len_check
                    if remaining_signal.end_index - signal.end_index >= signal_min_len and \
                            signal.start_index - remaining_signal.start_index >= signal_min_len:
                        new_signal = copy.deepcopy(remaining_signal)
                        new_signal.end_index = signal.start_index
                        remaining_signal.start_index = signal.end_index
                        signals.insert(signals.index(remaining_signal), new_signal)
                        remaining_signals.remove(remaining_signal)
                        print('test')
                    else:
                        pass
                if signal.start_index in remaining_signal or signal.end_index - 1 in remaining_signal:  # shorten
                    signal_min_len = [  # TODO need better way to check if signal can be shortened
                        rule for rule in self.rules if rule.rule_number is remaining_signal.signal_id
                    ][0].min_len_check
                    if signal.start_index - remaining_signal.start_index >= signal_min_len:
                        remaining_signal.end_index = signal.start_index
                        remaining_signals.remove(remaining_signal)
                    if remaining_signal.end_index - signal.end_index >= signal_min_len:
                        remaining_signal.start_index = signal.end_index
                        remaining_signals.remove(remaining_signal)
                    else:
                        signals_to_remove.append(remaining_signal)

                # if signal.end_index - 1 in remaining_signal:  # shorten
                #     signal_min_len = [  # TODO need better way to check if signal can be shortened
                #         rule for rule in self.rules if rule.rule_number is remaining_signal.signal_id
                #     ][0].min_len_check
                #     if remaining_signal.end_index - signal.end_index >= signal_min_len:
                #         remaining_signal.start_index = signal.end_index
                #         remaining_signals.remove(remaining_signal)
                #     else:
                #         signals_to_remove.append(remaining_signal)

        for signal_to_remove in signals_to_remove:
            try:
                signals.remove(signal_to_remove)
            except ValueError:
                pass
        return signals

    @staticmethod
    def _signals_to_ints(signals: List[Signal], data_length) -> List[int]:
        converted_signals = [0] * data_length
        for signal in signals:
            converted_signals[signal.start_index:signal.end_index] = [signal.signal_id] * len(signal)
        return converted_signals
