import io

from flask import Flask
from flask import render_template, jsonify, request, Response, url_for

from ccrev import config
from ccrev.charts.charts import IChart
from ccrev.config import TEST_DIR, CHART_TYPES
from ccrev.data_processing import Reviewer

app = Flask(__name__)


@app.route('/')
def index():
    files = app.config['reviewer'].source_files
    return render_template(
        'index.html',
        files=files,
        chart_types=sorted(CHART_TYPES.keys(), key=lambda x: str(x))
    )


@app.route('/_select_chart_change', methods=['POST'])
def _select_chart_type():
    req = request.json
    selected_chart_type = req['chartType']
    selected_chart = app.config['reviewer'].get_chart(src_file=req['chartSourceFileName'])

    res = {  # TODO shouldn't return img if nothings changed. should be able to load different chart type too
        'chartType': req['chartType'],
        'chartTitle': req['chartSourceFileName'],
        'chartPlotUrl': url_for('plot', chart_title=selected_chart.title, chart_type=selected_chart_type),
    }
    return jsonify(res)


@app.route('/<chart_title>_<chart_type>.png', methods=['GET'])
def plot(chart_title, chart_type):
    chart = app.config['reviewer'].get_chart(friendly_name=chart_title)

    if not isinstance(chart, CHART_TYPES[chart_type]):
        chart = CHART_TYPES[chart_type](chart)
        chart_index = app.config['reviewer'].friendly_names.index(chart_title)
        app.config['reviewer'].control_chart_data[chart_index] = chart

    if not chart.data:
        app.config['reviewer'].load_chart_data(chart=chart)

    plot: io.BytesIO = chart.save_plot_as_bytes
    return Response(plot.getvalue(), mimetype='image/png')


@app.route('/_move_chart_up', methods=['POST'])
def _move_chart_up():
    chart_title = request.json['chartTitle']
    res = {
        'chartTitle': chart_title,
        'chartBelowTitle': None
    }

    chart_index = app.config['reviewer'].friendly_names.index(chart_title)
    chart_above_index = chart_index - 1
    if chart_above_index >= 0:
        app.config['reviewer'].swap_chart_order(chart_index, chart_above_index)


@app.route('/_move_chart_down', methods=['POST'])
def _move_chart_down():
    chart_title = request.json['chartTitle']
    res = {
        'chartTitle': chart_title,
        'chartBelowTitle': None
    }

    chart_index = app.config['reviewer'].friendly_names.index(chart_title)
    chart_below_index = chart_index + 1
    if chart_below_index < len(app.config['reviewer'].control_chart_data):
        app.config['reviewer'].swap_chart_order(chart_index, chart_below_index)


@app.route('/_delete_chart', methods=['POST'])
def _delete_chart():
    chart = request.json['chartTitle']
    res = {
        'chartTitle': None,
    }
    try:
        del app.config['reviewer'].control_charts[chart]
        res['chartTitle'] = chart
    except ValueError:
        pass
    return jsonify(res)


if __name__ == '__main__':
    reviewer = Reviewer(**config.REVIEWER_KWARGS)
    reviewer.add_control_charts_from_directory(TEST_DIR, IChart)

    app: Flask
    app.config['reviewer']: Reviewer = reviewer
    app.env = 'development'
    app.debug = True

    app.run(host='127.0.0.1', port=5000, debug=True, load_dotenv=True)
