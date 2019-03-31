from __future__ import annotations

import io
import os
from abc import abstractmethod
from numbers import Number
from typing import List, Union, Any, Generator

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

    def __init__(self, x_labels=None):
        self.fig = Figure(Plot.FIG_SIZE)
        self.canvas = FigureCanvas(self.fig)
        self.axes: Axes = self.fig.add_subplot(Plot._SUBPLOT_GRID)
        self.x_labels = x_labels

    def add_line(self, y_data: List[Number], x_data: List[Number], **kwargs
                 ) -> None:
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
    def bytes(self) -> io.BytesIO:
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

    def show_signals(self, signals: List[int], x_data: List,
                     y_data: List[float]):
        if not signals:
            return

        x_data = [
            data_index if signal > 0 else 0
            for data_index, signal in zip(x_data, signals)
        ]
        y_data = [
            val if signal > 0 else 0
            for val, signal in zip(y_data, signals)
        ]
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
    def __init__(self, y_data=None, x_data=None, signals=None,
                 title=None, x_labels=None):

        self.title = title
        self.signals = signals

        self.mean_overwritten = False
        self.stdev_overwritten = False

        self._y_data: List[float] = y_data or []
        self._x_data = x_data or [idx for idx, _ in enumerate(self.y_data)]
        self._x_labels = x_labels

        self._stdev = self.stdev
        self._mean = self.mean

        self._x_min = self.x_min
        self._x_max = self.x_max
        self._y_min = self.y_min
        self._y_max = self.y_max

        self._data_start: int = None
        self._data_end: int = None

    @property
    @abstractmethod
    def plot(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def x_labels(self):
        raise NotImplementedError

    @x_labels.setter
    @abstractmethod
    def x_labels(self, val):
        raise NotImplementedError

    @property
    def y_data(self):
        y_data = None
        if isinstance(self._y_data, Generator):
            y_data = list(self._y_data)
            self.y_data = y_data
        else:
            y_data = self._y_data
        return y_data

    @y_data.setter
    def y_data(self, val):
        self._y_data = val

    @property
    def x_data(self):
        x_data = None
        if isinstance(self._x_data, Generator):
            x_data = list(self._x_data)
            self.x_data = x_data
        else:
            x_data = self._x_data
        return x_data

    @x_data.setter
    def x_data(self, val):
        self._x_data = val

    @property
    def data_start(self):
        return self._data_start

    @data_start.setter
    def data_start(self, val):
        self._data_start = self.x_data.index(self.nearest_x(val))

    @property
    def data_end(self):
        return self._data_end

    @data_end.setter
    def data_end(self, val):
        self._data_start = self.x_data.index(self.nearest_x(val))

    @property
    @abstractmethod
    def stdev(self):
        raise NotImplementedError

    @stdev.setter
    @abstractmethod
    def stdev(self, val):
        raise NotImplementedError

    @property
    @abstractmethod
    def mean(self):
        raise NotImplementedError

    @mean.setter
    @abstractmethod
    def mean(self, val):
        raise NotImplementedError

    @property
    def x_min(self):
        return self.plotted_x_data[0] if self.y_data else None

    @property
    def x_max(self):
        return self.plotted_x_data[len(self.plotted_x_data) - 1] if self.y_data\
            else None

    @property
    def y_min(self):
        return self.mean - 3.5 * self.stdev if self.y_data else None

    @property
    def y_max(self):
        return self.mean + 3.5 * self.stdev if self.y_data else None

    @classmethod
    def from_other_chart(cls, other_chart: ControlChart) -> ControlChart:
        return cls(
                y_data=other_chart.y_data,
                x_data=other_chart.x_data,
                title=other_chart.title,
        )

    @property
    @abstractmethod
    def center(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def upper_action_limit(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def lower_action_limit(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def upper_warning_limit(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def lower_warning_limit(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def plus_one_stdev(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def minus_one_stdev(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def plotted_x_data(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def plotted_y_data(self):
        raise NotImplementedError

    @abstractmethod
    def make_plot(self, show_signals=True) -> Plot:
        raise NotImplementedError

    @property
    def bytes(self) -> io.BytesIO:
        return self.plot.bytes

    @property
    def signals_in_chart(self) -> Union[List[int], None]:
        if not self.signals:
            return

        unique_signals = sorted(set(self.signals))
        try:
            unique_signals.remove(0)
        except ValueError:
            pass

        return unique_signals

    def save_as_jpeg(self, file_path: str):
        # TODO
        #  save where user specifies if dir path
        #  save in cwd if filename
        self.plot.save_as_jpeg(file_path)
        return os.path.abspath(os.path.join(os.getcwd(), file_path))

    def resize_plot_axes(self, x_min: float, x_max: float, y_min: float,
                         y_max: float) -> None:
        self.plot.resize_plot_axes(
                x_min=x_min,
                x_max=x_max,
                y_min=y_min,
                y_max=y_max,
        )

    def _format_plot(self, plot) -> None:
        plot.resize_plot_axes(
                self.x_min, self.x_max,
                self.y_min, self.y_max
        )

    def nearest_x(self, val) -> Any:
        return min(self.x_data, key=lambda x: abs(x - val))
