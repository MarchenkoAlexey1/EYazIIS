import os
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from search import search_query
from indexer import DOC_MAP_FILE
import joblib

EVAL_DATA_DIR = 'eval_data'
QUERIES_FILE = os.path.join(EVAL_DATA_DIR, 'queries.txt')
QRELS_FILE = os.path.join(EVAL_DATA_DIR, 'qrels.txt')
PLOT_FILE = os.path.join('static', 'images', 'evaluation_plot.png')


def load_qrels():
    qrels = {}
    with open(QRELS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            try:
                parts = line.split()
                if len(parts) == 4:
                    qid, _, doc_name, rel = parts
                    if qid not in qrels:
                        qrels[qid] = {}
                    qrels[qid][doc_name] = int(rel)
                else:
                    print(f"Предупреждение: неверный формат строки в qrels.txt: '{line}'")
            except ValueError:
                print(f"Предупреждение: не удалось разобрать строку в qrels.txt: '{line}'")
                continue

    return qrels


def load_queries():
    queries = {}
    with open(QUERIES_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split(':', 1)
            if len(parts) == 2:
                qid, query_text = parts
                queries[qid] = query_text.strip()
            else:
                print(f"Предупреждение: неверный формат строки в queries.txt: '{line}'")
    return queries


def calculate_metrics(retrieved_filenames, relevant_docs, total_docs_in_collection):
    retrieved_docs = retrieved_filenames
    retrieved_relevant_docs = [doc for doc in retrieved_docs if doc in relevant_docs]

    a = len(retrieved_relevant_docs)
    b = len(retrieved_docs) - a
    c = len(relevant_docs) - a

    total_non_relevant = total_docs_in_collection - len(relevant_docs)
    d = total_non_relevant - b

    precision = a / (a + b) if (a + b) > 0 else 0
    recall = a / (a + c) if (a + c) > 0 else 0
    f_measure = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    p_at_5 = len([doc for doc in retrieved_docs[:5] if doc in relevant_docs]) / 5
    p_at_10 = len([doc for doc in retrieved_docs[:10] if doc in relevant_docs]) / 10

    R = len(relevant_docs)
    r_precision = len([doc for doc in retrieved_docs[:R] if doc in relevant_docs]) / R if R > 0 else 0

    avg_prec = 0
    relevant_count = 0
    for i, doc in enumerate(retrieved_docs):
        if doc in relevant_docs:
            relevant_count += 1
            avg_prec += relevant_count / (i + 1)
    avg_prec = avg_prec / R if R > 0 else 0

    denominator = a + b + c + d
    accuracy = (a + d) / denominator if denominator > 0 else 0
    error = (b + c) / denominator if denominator > 0 else 0

    return {
        'precision': precision, 'recall': recall, 'f_measure': f_measure,
        'p_at_5': p_at_5, 'p_at_10': p_at_10,
        'r_precision': r_precision, 'avg_precision': avg_prec,
        'accuracy': accuracy, 'error': error
    }


def calculate_pr_curve(retrieved_filenames, relevant_docs):
    retrieved_docs = retrieved_filenames
    pr_points = []
    relevant_found = 0
    total_relevant = len(relevant_docs)
    if total_relevant == 0:
        return [(0, 1.0)]
    for i, doc in enumerate(retrieved_docs):
        if doc in relevant_docs:
            relevant_found += 1
            precision = relevant_found / (i + 1)
            recall = relevant_found / total_relevant
            pr_points.append((recall, precision))
    return pr_points


def interpolate_pr_curve(pr_points):
    recall_levels = np.linspace(0, 1, 11)
    interpolated_precision = []
    for r_level in recall_levels:
        max_p = 0
        for r, p in pr_points:
            if r >= r_level:
                if p > max_p:
                    max_p = p
        interpolated_precision.append(max_p)
    return recall_levels, interpolated_precision


def run_evaluation():
    queries = load_queries()
    qrels = load_qrels()

    try:
        doc_map = joblib.load(DOC_MAP_FILE)
        url_to_filename_map = {v['url']: v['filename'] for v in doc_map.values()}
        total_docs_count = len(doc_map)
    except FileNotFoundError:
        print("Ошибка: doc_map.pkl не найден. Запустите indexer.py.")
        return pd.DataFrame(), 0.0, None

    all_metrics = []
    all_interpolated_precisions = []

    for qid, query in queries.items():
        results, _ = search_query(query)

        result_filenames = [url_to_filename_map.get(res['url']) for res in results if
                            url_to_filename_map.get(res['url'])]

        relevant_docs = {doc for doc, rel in qrels.get(qid, {}).items() if rel > 0}

        if not relevant_docs:
            continue

        metrics = calculate_metrics(result_filenames, relevant_docs, total_docs_count)
        metrics['query_id'] = qid
        all_metrics.append(metrics)

        pr_points = calculate_pr_curve(result_filenames, relevant_docs)
        _, interpolated_p = interpolate_pr_curve(pr_points)
        all_interpolated_precisions.append(interpolated_p)

    if not all_metrics:
        return pd.DataFrame(), 0.0, None

    metrics_df = pd.DataFrame(all_metrics).set_index('query_id')

    mean_avg_precision = metrics_df['avg_precision'].mean() if 'avg_precision' in metrics_df.columns else 0.0

    if all_interpolated_precisions:
        mean_interpolated_p = np.mean(all_interpolated_precisions, axis=0)
        recall_levels = np.linspace(0, 1, 11)

        os.makedirs(os.path.dirname(PLOT_FILE), exist_ok=True)

        plt.figure(figsize=(8, 6))
        plt.plot(recall_levels, mean_interpolated_p, marker='o', linestyle='-')
        plt.title('11-Point Interpolated Precision-Recall Curve')
        plt.xlabel('Recall')
        plt.ylabel('Precision')
        plt.grid(True)
        plt.xlim([0, 1])
        plt.ylim([0, 1.05])
        plt.savefig(PLOT_FILE)
        plt.close()

    return metrics_df, mean_avg_precision, PLOT_FILE


if __name__ == '__main__':
    metrics_df, mean_ap, plot_path = run_evaluation()
    if not metrics_df.empty:
        print("--- Metrics per Query ---")
        print(metrics_df)
        print(f"\n--- Mean Average Precision (MAP) ---")
        print(f"{mean_ap:.4f}")
        if plot_path:
            print(f"\nGraph saved to {plot_path}")
    else:
        print("Evaluation could not be completed.")