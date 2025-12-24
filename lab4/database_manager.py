# database_manager.py
import sqlite3

class DictionaryDB:
    def __init__(self, db_file="custom_dictionary.db"):
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        """Создает таблицу, если она не существует."""
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS dictionary (
            id INTEGER PRIMARY KEY,
            english_word TEXT NOT NULL UNIQUE,
            german_translation TEXT NOT NULL,
            notes TEXT
        )
        """)
        self.conn.commit()

    def add_or_update_word(self, en_word, de_word, notes=""):
        """Добавляет или обновляет слово в словаре."""
        en_word = en_word.lower()
        self.cursor.execute("""
        INSERT INTO dictionary (english_word, german_translation, notes)
        VALUES (?, ?, ?)
        ON CONFLICT(english_word) DO UPDATE SET
        german_translation=excluded.german_translation,
        notes=excluded.notes
        """, (en_word, de_word, notes))
        self.conn.commit()

    def get_translation(self, en_word):
        """Получает перевод из пользовательского словаря."""
        en_word = en_word.lower()
        self.cursor.execute("SELECT german_translation FROM dictionary WHERE english_word=?", (en_word,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_all_words(self):
        """Возвращает все записи из словаря."""
        self.cursor.execute("SELECT english_word, german_translation, notes FROM dictionary ORDER BY english_word")
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()