import io
import urllib.parse
from typing import List

from flask import Flask
from flask import render_template, jsonify, request, Response, url_for

from ccrev import config
from ccrev.charts.charting_base import ControlChart
from ccrev.charts.charts import IChart
from ccrev.config import TEST_DIR, CHART_TYPES
from ccrev.data_processing import Reviewer

app = Flask(__name__)


@app.route('/')
def index():
    return render_template(
        'index.html',
        titles=app.config['reviewer'].chart_titles,
        chart_types=sorted(CHART_TYPES.keys(), key=lambda x: str(x))
    )


@app.route('/_set_chart_type', methods=['POST'])
def _set_chart_type():
    chart_title = request.json['chartTitle']
    selected_type = request.json['selectedType']
    currently_visible = request.json['currentlyVisible']

    chart_index = app.config['reviewer'].chart_titles.index(chart_title)
    chart = app.config['reviewer'].control_charts.index(chart_title)
    chart_type = type(app.config['reviewer'].control_charts.index(chart_index))

    update_plot = False
    if not isinstance(chart_type, CHART_TYPES[selected_type]):
        app.config['reviewer'].control_chart_data[chart_index][1] = CHART_TYPES[selected_type].from_other_chart(chart)
        update_plot = True

    return jsonify({'updatePlot': currently_visible and update_plot})


def _load_data(chart_title) -> None:
    control_charts: List[ControlChart] = app.config['reviewer'].control_charts
    chart_titles = app.config['reviewer'].chart_titles
    chart_index = chart_titles.index(chart_title)
    src_file = app.config['reviewer'].chart_src_files[chart_index]
    data_extractor = app.config['reviewer'].data_extractor
    control_charts[chart_index].y_data = data_extractor.get_excel_data(src_file)


@app.route('/show_chart', methods=['POST'])
def show_chart():
    chart_title = request.json['chartTitle']
    control_charts: List[ControlChart] = app.config['reviewer'].control_charts
    chart_titles = app.config['reviewer'].chart_titles
    chart_index = chart_titles.index(chart_title)
    not control_charts[chart_index].data and app.config['reviewer'].load_chart_data(chart_title=chart_title)
    return render_template(
            'plot.html',
            chart_title=chart_title,
            chartType=type(control_charts[chart_index]),
            plotUrl=url_for('plot', chart_title=f'{chart_title}')
    )


@app.route('/<chart_title>.png')
def plot(chart_title):
    chart_index = app.config['reviewer'].chart_titles.index(chart_title)
    plot = app.config['reviewer'].control_charts[chart_index].bytes
    return Response(plot.getvalue(), mimetype='image/png')


@app.route('/_move_chart', methods=['POST'])
def _move_chart():
    move_up = request.json['moveUp']
    titles = app.config['reviewer'].chart_titles
    chart_index = titles.index(request.json['chartTitle'])
    num_charts = len(titles)

    success = (move_up and chart_index > 0) or (not move_up and chart_index < num_charts - 1)
    success and move_up and app.config['reviewer'].move_chart_up(chart_index)
    success and not move_up and app.config['reviewer'].move_chart_down(chart_index)
    return jsonify({'success': success})


@app.route('/_delete_chart', methods=['POST'])
def _delete_chart():
    success = False
    try:
        chart_index = app.config['reviewer'].chart_titles.index(request.json['chartTitle'])
        del app.config['reviewer'].control_chart_data[chart_index]
        success = True
    except ValueError:
        pass
    finally:
        return jsonify({'success': success})


@app.route('/_upload', methods=['POST'])
def _upload():
    # TODO don't let upload file w/ duplicate title
    file = request.files['userfile']
    app.config['reviewer'].add_chart_from_file(
            src_file=io.BytesIO(file.read()),
            chart_type=IChart,
            title=app.config['reviewer'].data_extractor.clean_file_names(file.filename)
    )
    return render_template(
            'files.html',
            titles=app.config['reviewer'].chart_titles,
            chart_types=sorted(CHART_TYPES.keys(), key=lambda x: str(x))
    )


if __name__ == '__main__':
    reviewer = Reviewer(**config.REVIEWER_KWARGS)
    reviewer.add_control_charts_from_directory(TEST_DIR, IChart)

    app: Flask
    app.config['reviewer']: Reviewer = reviewer
    app.env = 'development'
    app.debug = True

    app.run(host='127.0.0.1', port=5000, debug=True, load_dotenv=True)
