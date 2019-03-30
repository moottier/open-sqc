import io
from datetime import datetime, date
from typing import Union, List, Any

from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak

from ccrev.charts.charting_base import ControlChart


class Report:
    """
    defines styling properties for PDF reports also
    provides an interface for adding content to PDFs
    """

    def __init__(self, name=date.today()):
        # reportlab template
        self.doc_template = SimpleDocTemplate

        # page formatting
        self.page_size = LETTER
        self.right_margin = 72
        self.left_margin = 72
        self.top_margin = 72
        self.bottom_margin = 72

        # paragraph styling
        self.report_styles = getSampleStyleSheet()
        self.report_styles.add(
                ParagraphStyle(
                        name='Left',
                        alignment=TA_LEFT,
                        leading=40
                )
        )
        self.font_size = 12

        # altering these during runtime may break program
        self._name = f'{name}.pdf'  # alter name via obj.name
        self._report = self.doc_template(
                self.name,
                pagesize=self.page_size,
                rightMargin=self.right_margin,
                leftMargin=self.left_margin,
                topmargin=self.top_margin,
                bottomMargin=self.bottom_margin
        )
        self._text = []

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, text):
        if str(text).endswith('.pdf'):
            self._name = f'{text}'
        else:
            self._name = f'{text}.pdf'

    def add_text(self, text):
        self._text.append(
                Paragraph(
                        f'<font size={self.font_size}>{text}</font>',
                        self.report_styles['Normal']
                )
        )

    def add_image(self, image_data: io.BytesIO):
        self._text.append(
                Image(image_data)
        )

    def add_spacer(self, height=1, width=12):
        self._text.append(Spacer(height, width))

    def add_page_break(self, num: int = 1):
        for _ in range(num):
            self._text.append(PageBreak())

    def save(self):
        self._report.build(self._text)

    def add_chart(self, chart: ControlChart, chart_comments: str = None, *,
                  signal_labels: Union[List[Any], None] = None) -> None:
        self.add_text(chart.title)
        self.add_spacer()
        self.add_image(chart.bytes)
        self.add_spacer()
        if chart.signals_in_chart:
            for signal_id in chart.signals_in_chart:
                signal_str = self.stringify_signals(signal_id, chart, labels=signal_labels)
                self.add_text(f'{signal_id}: {signal_str}')
                self.add_spacer()
        else:
            self.add_text('No signals found.')
        self.add_spacer()
        if chart_comments:
            self.add_text('Reviewer comments: %s' % chart_comments)
        self.add_page_break()

    @staticmethod
    def stringify_signals(signal_id: int, chart: ControlChart, labels: Union[List[Any], None] = None) -> str:
        """
        return a string of the plotted indices where there are signals
        sequential signals are hyphenated (i.e. [1,1,0,1] -> '0 - 1, 3')
        """

        def short_str(dt: datetime) -> str:
            dt = dt.month, dt.day, dt.hour, dt.minute
            dt = (str(val) for val in dt)
            dt = (f'0{val}' if len(val) is 1 else val for val in dt)  # prepend '0' to single-char strings
            return '%s/%s %s:%s' % tuple(dt)  # mm/dd hh:mm

        target_signal = signal_id
        if target_signal not in chart.signals_in_chart:
            return 'No signals found.'

        signals = list(signal_id if signal_id in (0, target_signal) else 0 for signal_id in chart.signals)
        labels = labels if labels else chart.plotted_x_data
        labels = [short_str(val) if isinstance(val, datetime) else val for val in labels]

        s: str = ''
        start: Union[int, None] = None
        for idx, (label, signal) in enumerate(zip(labels, signals)):
            if signal:
                if start is not None:  # continue consecutive signals
                    if idx is len(signals) - 1:  # end of signals sequence
                        s += f' - {label}'
                    else:
                        continue
                else:
                    s += f'{label}'
                    start = idx
            else:
                if start is not None:  # end consecutive signals
                    if idx - start is 1:  # lone signal
                        s += ', '
                    if idx - start > 1:
                        s += f' - {labels[idx - 1]}, '
                    start = None
        return s
