import statistics
from typing import List

from ccrev import config
from ccrev.charts.charting_base import ControlChart, Plot


class IChart(ControlChart):
    def __init__(self, y_data, x_data=None, signals=None, title=None, **kwargs):
        super().__init__(y_data, x_data, signals, title, **kwargs)

        self.signals: List[int] = signals

    def __str__(self):
        return f'IChart: {self.title} {zip(self.plotted_x_data, self.plotted_y_data)[:5]}'

    @property
    def stdev(self):
        return statistics.stdev(self.y_data) if self.y_data else None

    @stdev.setter
    def stdev(self, val):
        self._stdev = val

    @property
    def mean(self):
        return statistics.mean(self.y_data) if self.y_data else None

    @mean.setter
    def mean(self, val):
        self._mean = val

    @property
    def plotted_y_data(self):
        """data sometimes needs to be transformed before plotting"""
        return self.y_data

    @property
    def plotted_x_data(self):
        """data_index sometimes needs to be transformed before plotting"""
        return [idx for idx, val in enumerate(self.plotted_y_data, start=1)]

    @property
    def center(self):
        return [self.mean] * len(self.plotted_x_data)

    @property
    def upper_action_limit(self):
        return [self.mean + 3 * self.stdev] * len(self.plotted_x_data)

    @property
    def lower_action_limit(self):
        return [self.mean - 3 * self.stdev] * len(self.plotted_x_data)

    @property
    def upper_warning_limit(self):
        return [self.mean + 2 * self.stdev] * len(self.plotted_x_data)

    @property
    def lower_warning_limit(self):
        return [self.mean - 2 * self.stdev] * len(self.plotted_x_data)

    @property
    def plus_one_stdev(self):
        return [self.mean + self.stdev] * len(self.plotted_x_data)

    @property
    def minus_one_stdev(self):
        return [self.mean - self.stdev] * len(self.plotted_x_data)

    def make_plot(self, show_signals=True) -> Plot:
        self.plot = Plot()
        # TODO 
        #  create dict instance attr that these calls pull values from  
        #  would allow for more customization of charts
        self.plot.add_line(self.plotted_y_data, x_data=self.plotted_x_data, color='b')
        self.plot.add_line(self.center, x_data=self.plotted_x_data, color='k')
        self.plot.add_line(self.upper_action_limit, x_data=self.plotted_x_data, color='r')
        self.plot.add_line(self.lower_action_limit, x_data=self.plotted_x_data, color='r')
        self.plot.add_line(self.upper_warning_limit, x_data=self.plotted_x_data, color=config.ORANGE)  # orange
        self.plot.add_line(self.lower_warning_limit, x_data=self.plotted_x_data, color=config.ORANGE)
        self.plot.add_line(self.plus_one_stdev, x_data=self.plotted_x_data, color='g')
        self.plot.add_line(self.minus_one_stdev, x_data=self.plotted_x_data, color='g')

        if show_signals:
            self.plot.show_signals(self.signals, self.plotted_y_data, self.plotted_x_data)

        self.format_plot()

        return self.plot
