import datetime
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image

from ccrev.charts.chart_base import ControlChart


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
                alignment=TA_LEFT
                )
            )
        self.font_size = 12

        # altering these during runtime may break program
        self._name = f'{name}.pdf'  # alter name via obj.name
        self._report = None
        self._text = []

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, text):
        if text.endswith('.pdf'):
            self._name = f'{text}'
        else:
            self._name = f'{text}.pdf'

    def configure(self):
        self._report = self.doc_template(
            self.name,
            pagesize=self.page_size,
            rightMargin=self.right_margin,
            leftMargin=self.left_margin,
            topmargin=self.top_margin,
            bottomMargin=self.bottom_margin
        )
        return self

    def add_text(self, text):
        self._text.append(
            Paragraph(
                f'<font size={self.font_size}>{text}</font>',
                self.report_styles['Normal']
            )
        )

    def add_image(self, file_name):
        self._text.append(
            Image(file_name)
        )

    def add_spacer(self, height=1, width=12):
        self._text.append(Spacer(height, width))

    def add_chart(self, chart: ControlChart):
        self.add_text(chart.title)
        self.add_spacer()
        self.add_image(chart.save_plot_as_jpeg())

    def save(self):
        self._report.build(self._text)


