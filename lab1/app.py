from flask import Flask, render_template, request, url_for
from search import search_query
from evaluation import run_evaluation
import time

app = Flask(__name__)


@app.url_defaults
def add_cache_buster(endpoint, values):
    if 'filename' in values and endpoint == 'static':
        values['c'] = int(time.time())


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return render_template('results.html', query=query, results=[], error="Please enter a query.")

    results, error = search_query(query)
    return render_template('results.html', query=query, results=results, error=error)


@app.route('/evaluate')
def evaluate():
    try:
        metrics_df, map_score, plot_path = run_evaluation()
        metrics_table = metrics_df.to_html(classes='table table-striped', float_format='{:.4f}'.format)
        return render_template('evaluation.html', map_score=map_score, metrics_table=metrics_table, plot_path=plot_path)
    except FileNotFoundError:
        return "Evaluation data not found. Please create `queries.txt` and `qrels.txt` in the `eval_data` directory, and run the indexer."
    except Exception as e:
        return f"An error occurred during evaluation: {e}"


if __name__ == '__main__':
    app.run(debug=True)