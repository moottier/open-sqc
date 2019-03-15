from __future__ import annotations

import io
import os
import datetime
from abc import abstractmethod
from numbers import Number
from typing import List

from matplotlib.axes import Axes
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.lines import Line2D


class Plot:
    """
    wrapper and interface for matplotlib canvas to
    include in reports
    """
    FIG_SIZE = (FIG_WIDTH, FIG_HEIGHT) = 6, 3  # in inches

    PLOT_COLS = PLOT_ROWS = PLOT_POS = 1
    _SUBPLOT_GRID = int(str(PLOT_ROWS) + str(PLOT_COLS) + str(PLOT_POS))

    def __init__(self, name=None):
        self.name = name
        self.fig = Figure(Plot.FIG_SIZE)
        self.canvas = FigureCanvas(self.fig)
        self.axes: Axes = self.fig.add_subplot(Plot._SUBPLOT_GRID)

    def add_line(self, y_data: List[Number], x_data: List[Number], **kwargs) -> None:
        """
        add a line to the plot
        """
        new_line = Line2D(
            xdata=x_data,
            ydata=y_data,
            **kwargs
        )
        self.axes.add_line(new_line)

    @property
    def as_byres(self) -> io.BytesIO:
        image_data = io.BytesIO()
        self.fig.savefig(image_data, format='png')
        image_data.seek(0)
        return image_data

    def resize_plot_axes(self, x_min, x_max, y_min, y_max):
        self.axes.set_xlim(x_min, x_max)
        self.axes.set_ylim(y_min, y_max)

    def save_as_jpeg(self, file_path: str):
        if file_path.endswith('jpeg'):
            self.canvas.print_jpeg(file_path)
        else:
            self.canvas.print_jpeg(f'{file_path}.jpeg')

    def show_signals(self, signals: List[int], plotted_data_index: List, plotted_data: List[float]):
        if not signals:
            return

        x_data = [data_index if signal > 0 else 0 for data_index, signal in zip(plotted_data_index, signals)]
        y_data = [val if signal > 0 else 0 for val, signal in zip(plotted_data, signals)]
        while True:
            try:
                x_data.remove(0)
                y_data.remove(0)
            except ValueError:
                break  # remove until none left

        self.add_line(
            x_data=x_data,
            y_data=y_data,
            color='r',
            marker='o',
            markersize=2.2,
            linestyle='None'
        )


class ControlChart:
    # TODO interface to data should be cls.data and cls.plot_data same for index & signals
    def __init__(self, src_file, data, data_index=None, signals=None, title=None, *, st_dev=None, mean=None,
                 plot_against_provided_index: bool=True, index_dates_short_format: bool=True):
        self.title = title
        self._src_file = src_file
        self.standard_deviation = None
        self.mean = None
        self.signals = signals

        self._data: List[float] = data
        self._data_index = data_index

        self._plot_factory = Plot

        # CONFIG SETTINGS
        self.plot_against_provided_index = plot_against_provided_index
        self.index_dates_short_format = index_dates_short_format

        self.is_stale = False

        #TODO create st_dev & mean property. should be loadable or calculable
        # mark as stale if data updated amd st_dev not updated

    @classmethod
    def from_other_chart(cls, other_chart: ControlChart) -> ControlChart:
        return cls(
            data=other_chart._data,
            data_index=other_chart._data_index,
            signals=other_chart.signals,
            title=other_chart.title,
            st_dev=other_chart.standard_deviation,
            mean=other_chart.mean,
            plot_against_provided_index=other_chart.plot_against_provided_index,
            index_dates_short_format=other_chart.index_dates_short_format
        )

    @abstractmethod
    def plot(self, show_signals=True) -> Plot:
        raise NotImplementedError

    @property
    def save_plot_as_bytes(self) -> io.BytesIO:
        # TODO remove 'self.plot: Plot' ?
        self.plot: Plot  # for pycharm completion
        return self.plot.as_byres

    def save_plot_as_jpeg(self, file_path: str):
        plot: Plot = self.plot  # TODO had to write like this to make pycharm typecheck shut up
        plot.save_as_jpeg(file_path)
        return os.path.abspath(os.path.join(os.getcwd(), file_path))

    @property
    def data(self) -> List:
        return self._data

    @data.setter
    def data(self, vals):
        self._data = vals

    @property
    def raw_data_index(self) -> List:
        return self._data_index if self._data_index else list(val for val in range(len(self.data)))

    @raw_data_index.setter
    def raw_data_index(self, vals):
        self._data = vals

    @property
    @abstractmethod
    def plotted_data(self):
        """data sometimes needs to be transformed before plotting"""
        raise NotImplementedError

    @plotted_data.setter
    @abstractmethod
    def plotted_data(self, vals):
        raise NotImplementedError

    @property
    @abstractmethod
    def plotted_data_index(self):
        """data_index sometimes needs to be transformed before plotting"""
        raise NotImplementedError

    @plotted_data_index.setter
    @abstractmethod
    def plotted_data_index(self, vals):
        raise NotImplementedError

    @property
    def signals_in_chart(self):
        if not self.signals:
            return

        unique_signals = sorted(set(self.signals))
        # TODO looks self.signals is being assigned incorrectly
        try:
            unique_signals.remove(0)
        except ValueError:
            pass

        return unique_signals

    def stringify_signals(self, tgt_signal_id: int, signal_dates_short_format: bool=True) -> str:
        """
        return a string of the plotted indices where there are signals
        sequential signals are hyphenated (i.e. [1,1,0,1] -> '0 - 1, 3')
        """
        def datetime_to_short_str(dt: datetime.datetime) -> str:
            return '%s/%s %s:%s' % (dt.month, dt.day, dt.hour, dt.minute)

        signals = list(signal_id for signal_id in self.signals if signal_id in (0, tgt_signal_id))

        if not signals:
            return 'No signals.'

        signal_str = ''
        signal_start = None
        for iter_pos, signal_index, signal in zip(range(len(signals)), self.plotted_data_index, signals):
            # TODO this is ugly AF
            if signal:
                if signal_start is not None:
                    if iter_pos is len(signals) - 1:
                        signal_index = self.plotted_data_index[iter_pos]
                        signal_str += ' - %s' % datetime_to_short_str(signal_index) if \
                            isinstance(signal_index, datetime.datetime) and signal_dates_short_format else signal_index
                    else:
                        continue
                else:
                    signal_str += '%s' % datetime_to_short_str(signal_index) if \
                            isinstance(signal_index, datetime.datetime) and signal_dates_short_format else signal_index
                    signal_start = iter_pos
            else:
                if signal_start is not None:
                    if iter_pos - signal_start is 1:
                        signal_str += ', '
                    if iter_pos - signal_start > 1:
                        signal_index = self.plotted_data_index[iter_pos - 1]
                        signal_str += ' - %s, ' % datetime_to_short_str(signal_index) if \
                            isinstance(signal_index, datetime.datetime) and signal_dates_short_format else signal_index
                    signal_start = None

        return signal_str
