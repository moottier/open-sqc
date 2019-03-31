import copy
import itertools
from typing import Sequence, Type, List, Any, Union, Tuple

from ccrev.rules import Rule, Signal


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
    ) -> Union[List[Signal], List[int]]:
        """
        driver for rule-checking routine
        """

        signal: Signal = None
        for data_index, datum in enumerate(data):
            # if signal already detected at data_index
            pass
            if self._signals and any(data_index in signal for signal in self._signals):
                if signal:
                    self._signals.append(signal)
                    # update signal list and
                    # clear signal if signal detected for data index
                    signal = None
                continue  # skip data_index

            if signal:
                min_len_continuation_check = rule.min_len_continuation_check or 0
                # TODO, why need pass signal._is_positive && signal??
                if rule.is_continued(
                        data[data_index - min_len_continuation_check:data_index + 1],
                        signal._is_positive,
                        signal,
                        **stats_data
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
    def check_all_rules(self, data, **stats_data) -> List[int]:
        signals = []
        for rule in self.rules:
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
        def split(signal: Signal, index: int) -> Tuple[Signal, Signal]:
            new_signal = copy.deepcopy(signal)
            new_signal.start_index = index
            signal.end_index = index

            return signal, new_signal

        def is_shortenable(signal: Signal, overlap_start_pos: int, overlap_end_pos: int) -> bool:
            signal_min_len = [rule.min_len_check for rule in self.rules if rule.rule_number is signal.signal_id][0]
            overlap_len = overlap_end_pos - overlap_start_pos

            return len(signal) - overlap_len >= signal_min_len

        signals_to_remove = []
        for signal_index, signal in enumerate(signals):
            remaining_signals = signals[signal_index + 1:]
            for remaining_signal in remaining_signals:
                if remaining_signal.signal_id is signal.signal_id:
                    continue  # signals of same priority cannot (should not) be overlapped

                # start/end of low priority signal overlapped by high priority
                is_overlapped_start = signal.end_index - 1 in remaining_signal
                is_overlapped_end = signal.start_index in remaining_signal

                # lower priority signal can be shortened at front/end
                is_shortenable_start = is_overlapped_start and \
                                       is_shortenable(
                                           remaining_signal,
                                           remaining_signal.start_index,
                                           signal.end_index
                                       )
                is_shortenable_end = is_overlapped_end and \
                                     is_shortenable(
                                         remaining_signal,
                                         signal.start_index,
                                         remaining_signal.end_index
                                     )

                # 1 1 0 1 1 1 0 0
                # 2 2 2 2 0 2 2 2

                if is_shortenable_end and is_shortenable_start:
                    remaining_signal, new_signal = split(remaining_signal, signal.end_index)
                    signals.insert(signals.index(remaining_signal), new_signal)
                    remaining_signals.insert(remaining_signals.index(remaining_signal), new_signal)
                elif is_shortenable_end and not is_shortenable_start:
                    remaining_signal.end_index = signal.start_index
                elif is_shortenable_start and not is_shortenable_end:
                    remaining_signal.start_index = signal.end_index

                if (is_overlapped_end or is_overlapped_start) and not (is_shortenable_start or is_shortenable_end):
                    signals_to_remove.append(remaining_signal)

        for signal_to_remove in set(signals_to_remove):
            signals.remove(signal_to_remove)

        return signals

    @staticmethod
    def _signals_to_ints(signals: List[Signal], data_length) -> List[int]:
        converted_signals = [0] * data_length
        for signal in signals:
            converted_signals[signal.start_index:signal.end_index] = [signal.signal_id] * len(signal)

        return converted_signals
