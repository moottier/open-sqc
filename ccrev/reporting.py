import datetime
import io

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

    def __init__(self, name=datetime.date.today()):
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
            # TODO why is datetime.datetime making it here
            # if text.endswith('.pdf'):
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

    def add_chart(self, chart: ControlChart, chart_comments: str = None, *, signal_dates_short_format: bool=True) -> None:
        self.add_text(chart.title)
        self.add_image(chart.save_plot_as_bytes)  # TODO better save path and cleanup files afterwards
        self.add_spacer()
        if chart.signals_in_chart:
            for signal_id in chart.signals_in_chart:
                self.add_text('%s: %s' % (signal_id, chart.stringify_signals(signal_id, signal_dates_short_format)))
                self.add_spacer()
        else:
            self.add_text('No signals found.')
        self.add_spacer()
        if chart_comments:
            self.add_text('Reviewer comments: %s' % chart_comments)
        self.add_page_break()

    def save(self):
        self._report.build(self._text)
