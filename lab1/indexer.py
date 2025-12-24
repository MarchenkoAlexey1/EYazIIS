import os
from sklearn.feature_extraction.text import TfidfVectorizer
import joblib
from tokenizer import spacy_tokenizer

DATA_DIR = 'data'
CRAWLED_FILES_DIR = os.path.join(DATA_DIR, 'crawled')
INDEX_FILE = os.path.join(DATA_DIR, 'tfidf_index.pkl')
VECTORIZER_FILE = os.path.join(DATA_DIR, 'tfidf_vectorizer.pkl')
DOC_MAP_FILE = os.path.join(DATA_DIR, 'doc_map.pkl')


def create_index():
    if not os.path.exists(CRAWLED_FILES_DIR):
        print("Crawled data not found. Please run crawler.py first.")
        return

    documents = []
    doc_map = {}  # Maps index to filename and URL

    doc_files = sorted(os.listdir(CRAWLED_FILES_DIR))
    for i, filename in enumerate(doc_files):
        filepath = os.path.join(CRAWLED_FILES_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            url = f.readline().strip()
            content = f.read()
            documents.append(content)
            doc_map[i] = {'filename': filename, 'url': url}

    if not documents:
        print("No documents to index.")
        return

    vectorizer = TfidfVectorizer(tokenizer=spacy_tokenizer)
    tfidf_matrix = vectorizer.fit_transform(documents)

    joblib.dump(tfidf_matrix, INDEX_FILE)
    joblib.dump(vectorizer, VECTORIZER_FILE)
    joblib.dump(doc_map, DOC_MAP_FILE)

    print(f"Indexing complete. Indexed {len(documents)} documents.")
    print(f"Vocabulary size: {len(vectorizer.get_feature_names_out())}")


if __name__ == '__main__':
    create_index()