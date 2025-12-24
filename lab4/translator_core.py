# translator_core.py
from transformers import pipeline
import spacy
from collections import Counter
from database_manager import DictionaryDB
import re


class Translator:
    def __init__(self):
        print("Загрузка моделей... Это может занять некоторое время.")
        # Загрузка модели перевода
        self.translator_pipeline = pipeline("translation_en_to_de", model="Helsinki-NLP/opus-mt-en-de")
        # Загрузка модели spaCy
        self.nlp = spacy.load("en_core_web_sm")
        # Подключение к БД
        self.db = DictionaryDB()
        print("Модели успешно загружены.")

    def process_text(self, text: str):
        """
        Полный цикл обработки текста: анализ, перевод, сбор статистики.
        """
        # 1. Анализ текста с помощью spaCy
        doc = self.nlp(text)

        # 2. Подсчет слов (исключаем пунктуацию и пробелы)
        words = [token for token in doc if token.is_alpha]
        total_words_count = len(words)

        # 3. Полный перевод текста (здесь модель работает отлично, так как есть контекст)
        full_translation = self.translator_pipeline(text)[0]['translation_text']

        # 4. Создание частотного списка слов
        # Собираем пары (лемма, POS-тег), чтобы различать usage (use-noun vs use-verb)
        lemma_counts = Counter()
        lemma_pos_map = {}  # Словарь для хранения описания POS

        for token in words:
            if token.pos_ == "PROPN":
                lemma = token.lemma_
            else:
                lemma = token.lemma_.lower()

            if lemma not in lemma_counts:
                lemma_pos_map[lemma] = (token.pos_, spacy.explain(token.pos_))
            lemma_counts[lemma] += 1

        # 5. Сбор грамматической информации и перевод отдельных слов
        word_details = []
        # Сортируем по частоте
        sorted_lemmas = sorted(lemma_counts.keys(), key=lambda k: lemma_counts[k], reverse=True)

        for lemma in sorted_lemmas:
            pos_tag, pos_desc = lemma_pos_map.get(lemma, ("X", "Unknown"))

            # АЛГОРИТМ ПОЛУЧЕНИЯ ПЕРЕВОДА:
            # 1. Проверяем пользовательский словарь (БД)
            custom_translation = self.db.get_translation(lemma)

            if custom_translation:
                final_translation = custom_translation
            else:
                # 2. Если нет в БД, используем "Умный перевод" с контекстом
                final_translation = self._smart_translate_word(lemma, pos_tag)

            word_details.append({
                "word": lemma,
                "frequency": lemma_counts[lemma],
                "pos_tag": pos_tag,
                "pos_desc": pos_desc,
                "translation": final_translation
            })

        return {
            "original_text": text,
            "translated_text": full_translation,
            "total_words": total_words_count,
            "word_details": word_details,
            "spacy_doc": doc
        }

    def _smart_translate_word(self, lemma, pos_tag):
        """
        Пытается улучшить перевод отдельного слова, добавляя искусственный контекст
        в зависимости от части речи.
        """
        try:
            # Игнорируем слишком короткие слова или мусор, если они не в словаре
            if len(lemma) < 2 and lemma not in ['a', 'i']:
                raw_trans = self.translator_pipeline(lemma)[0]['translation_text']
                return raw_trans

            translation = ""

            if pos_tag == "NOUN":
                # Добавляем артикль, чтобы модель поняла, что это существительное
                # "art" -> "the art" -> "die Kunst"
                input_str = f"the {lemma}"
                raw = self.translator_pipeline(input_str)[0]['translation_text']

                # Убираем немецкие артикли из начала строки
                # (der, die, das, dem, den, des, ein, eine...)
                # Регулярное выражение удаляет первое слово, если это артикль
                translation = re.sub(r'^(die|der|das|dem|den|des|ein|eine|einen)\s+', '', raw, flags=re.IGNORECASE)

                # Если перевод превратился в "Art.-Nr." из-за "the art", это сложнее,
                # но "the art" гораздо реже переводится как "Art.-Nr." чем просто "art".

            elif pos_tag == "VERB":
                # Добавляем "to", чтобы получить инфинитив
                # "star" -> "to star" -> "zu spielen" (или "zu starren")
                input_str = f"to {lemma}"
                raw = self.translator_pipeline(input_str)[0]['translation_text']
                # Убираем "zu " из начала
                translation = re.sub(r'^(um\s+)?(zu|zum)\s+', '', raw, flags=re.IGNORECASE)

            elif pos_tag == "ADJ":
                # Добавляем "very", чтобы усилить контекст прилагательного
                # "red" -> "very red" -> "sehr rot"
                input_str = f"very {lemma}"
                raw = self.translator_pipeline(input_str)[0]['translation_text']
                translation = re.sub(r'^sehr\s+', '', raw, flags=re.IGNORECASE)

            else:
                # Для остальных частей речи (или если не сработали условия) переводим как есть
                translation = self.translator_pipeline(lemma)[0]['translation_text']

            # --- Блок защиты от галлюцинаций ---
            # Если перевод стал слишком длинным по сравнению с исходником (например, ought -> диалог),
            # или содержит странные символы, возвращаем сырой перевод или оригинал.
            if len(translation) > len(lemma) * 5:
                # Скорее всего галлюцинация
                return f"[{translation[:20]}...]"

                # Очистка от лишних пробелов и точек
            translation = translation.strip(" .")
            return translation

        except Exception:
            # Если что-то пошло не так, возвращаем простой перевод
            return self.translator_pipeline(lemma)[0]['translation_text']

    def get_dependency_parse(self, sentence_text: str):
        """Строит текстовое представление дерева синтаксического разбора."""
        doc = self.nlp(sentence_text)
        tree = []
        for token in doc:
            tree.append(
                f"{token.text:<15} {token.pos_:<10} {token.dep_:<15} {token.head.text}"
            )
        return "\n".join(tree)

    def close_db(self):
        self.db.close()