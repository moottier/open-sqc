from typing import List

from ccrev import config
from ccrev.charts.charting_base import ControlChart, Plot


class IChart(ControlChart):
    def __init__(self, src_file, data, data_index=None, signals=None, title=None, *, st_dev=None, mean=None, **kwargs):
        super().__init__(src_file, data, data_index, signals, title, st_dev=st_dev, mean=mean)

        self.standard_deviation: float = st_dev
        self.mean: float = mean
        self.signals: List[int] = signals

    def __str__(self):
        return 'IChart: %s' % self.title if self.title else 'IChart: %s' % self.plotted_data[:5]

    def __repr__(self):
        return 'IChart: %s' % self.title if self.title else 'IChart: %s' % self.plotted_data[:5]

    @property
    def plotted_data(self):
        """data sometimes needs to be transformed before plotting"""
        return self.data

    @plotted_data.setter
    def plotted_data(self, vals):
        self._data = vals

    @property
    def plotted_data_index(self):
        """data_index sometimes needs to be transformed before plotting"""
        return self.raw_data_index

    @plotted_data_index.setter
    def plotted_data_index(self, vals):
        self._data_index = vals

    @property
    def center(self):
        return [self.mean] * len(self.plotted_data)

    @property
    def upper_action_limit(self):
        return [self.mean + 3 * self.standard_deviation] * len(self.plotted_data)

    @property
    def lower_action_limit(self):
        return [self.mean - 3 * self.standard_deviation] * len(self.plotted_data)

    @property
    def upper_warning_limit(self):
        return [self.mean + 2 * self.standard_deviation] * len(self.plotted_data)

    @property
    def lower_warning_limit(self):
        return [self.mean - 2 * self.standard_deviation] * len(self.plotted_data)

    @property
    def plus_one_standard_deviation(self):
        return [self.mean + self.standard_deviation] * len(self.plotted_data)

    @property
    def minus_one_standard_deviation(self):
        return [self.mean - self.standard_deviation] * len(self.plotted_data)

    @property
    def plot(self, show_signals=True) -> Plot:
        plot = self._plot_factory()
        if self.plot_against_provided_index:
            plot.add_line(self.plotted_data, x_data=self.plotted_data_index, color='b')
            plot.add_line(self.center, x_data=self.plotted_data_index, color='k')
            plot.add_line(self.upper_action_limit, x_data=self.plotted_data_index, color='r')
            plot.add_line(self.lower_action_limit, x_data=self.plotted_data_index, color='r')
            plot.add_line(self.upper_warning_limit, x_data=self.plotted_data_index, color=config.ORANGE)  # orange
            plot.add_line(self.lower_warning_limit, x_data=self.plotted_data_index, color=config.ORANGE)
            plot.add_line(self.plus_one_standard_deviation, x_data=self.plotted_data_index, color='g')
            plot.add_line(self.minus_one_standard_deviation, x_data=self.plotted_data_index, color='g')
            if show_signals:
                plot.show_signals(self.signals, self.plotted_data_index, self.plotted_data)
        # TODO this amount of code repeating makes me want to shoot myself
        else:
            data_index = [val for val in range(len(self.plotted_data))]
            plot.add_line(self.plotted_data, x_data=data_index, color='b')
            plot.add_line(self.center, x_data=data_index, color='k')
            plot.add_line(self.upper_action_limit, x_data=data_index, color='r')
            plot.add_line(self.lower_action_limit, x_data=data_index, color='r')
            plot.add_line(self.upper_warning_limit, x_data=data_index, color=config.ORANGE)  # orange
            plot.add_line(self.lower_warning_limit, x_data=data_index, color=config.ORANGE)
            plot.add_line(self.plus_one_standard_deviation, x_data=data_index, color='g')
            plot.add_line(self.minus_one_standard_deviation, x_data=data_index, color='g')
            if show_signals:
                plot.show_signals(self.signals, data_index, self.plotted_data)
                
        plot.resize_plot_axes(
            x_min=0,
            x_max=len(self.plotted_data),
            y_min=self.center[0] - 3.5 * self.standard_deviation,
            y_max=self.center[0] + 3.5 * self.standard_deviation
        )
        return plot
