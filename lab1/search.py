import joblib
from sklearn.metrics.pairwise import cosine_similarity
from tokenizer import spacy_tokenizer
from indexer import INDEX_FILE, VECTORIZER_FILE, DOC_MAP_FILE
import numpy as np

try:
    tfidf_matrix = joblib.load(INDEX_FILE)
    vectorizer = joblib.load(VECTORIZER_FILE)
    doc_map = joblib.load(DOC_MAP_FILE)
    if vectorizer:
        terms = vectorizer.get_feature_names_out()
    else:
        terms = None
except FileNotFoundError:
    tfidf_matrix, vectorizer, doc_map, terms = None, None, None, None


def search_query(query):
    if not all([tfidf_matrix is not None, vectorizer is not None, doc_map is not None, terms is not None]):
        return [], "Index not found. Please run indexer.py."

    query_tokens_with_pos = spacy_tokenizer(query)
    if not query_tokens_with_pos:
        return [], "Please enter a valid query."

    candidate_doc_indices = set(range(tfidf_matrix.shape[0]))

    for token in query_tokens_with_pos:
        if token in vectorizer.vocabulary_:
            term_index = vectorizer.vocabulary_[token]
            docs_with_term = set(tfidf_matrix[:, term_index].nonzero()[0])
            candidate_doc_indices &= docs_with_term
        else:
            clean_token = token.split('_')[0]
            return [], f"Term '{clean_token}' in its context not found. No results possible."

    if not candidate_doc_indices:
        return [], "No documents match all query terms."

    final_candidate_list = list(candidate_doc_indices)
    query_vec = vectorizer.transform([query])
    candidate_matrix = tfidf_matrix[final_candidate_list, :]
    scores = cosine_similarity(query_vec, candidate_matrix).flatten()
    sorted_inner_indices = np.argsort(scores)[::-1]

    results = []
    clean_query_tokens = [t.split('_')[0] for t in query_tokens_with_pos]

    for i in sorted_inner_indices:
        doc_id = final_candidate_list[i]
        score = scores[i]

        results.append({
            'url': doc_map[doc_id]['url'],
            'score': score,
            'found_words': clean_query_tokens
        })

    return results, None