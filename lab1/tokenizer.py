import spacy

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading 'en_core_web_sm' model...")
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")


def spacy_tokenizer(document):

    tokens = nlp(document)

    meaningful_pos_tags = ['NOUN', 'PROPN', 'VERB', 'ADJ']

    return [
        f"{token.lemma_.lower()}_{token.pos_}" for token in tokens
        if not token.is_stop and not token.is_punct and not token.is_space and token.pos_ in meaningful_pos_tags
    ]