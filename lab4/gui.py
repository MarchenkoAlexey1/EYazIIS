# gui.py
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, simpledialog
from translator_core import Translator


class TranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Система Машинного Перевода")
        self.root.geometry("1000x700")

        self.translator = Translator()
        self.last_result = None

        self._setup_ui()

    def _setup_ui(self):
        # ... (весь код до setup_menu() остается без изменений) ...

        # Основной фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Панель ввода/вывода
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True, pady=10)

        # Левая панель (ввод)
        left_frame = ttk.Frame(paned_window, padding="5")
        ttk.Label(left_frame, text="Введите текст на английском:").pack(anchor="w")
        self.text_in = scrolledtext.ScrolledText(left_frame, wrap=tk.WORD, height=10)
        self.text_in.pack(fill=tk.BOTH, expand=True)
        paned_window.add(left_frame, weight=1)

        # Правая панель (вывод)
        right_frame = ttk.Frame(paned_window, padding="5")
        ttk.Label(right_frame, text="Перевод на немецкий:").pack(anchor="w")
        self.text_out = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, height=10, state="disabled")
        self.text_out.pack(fill=tk.BOTH, expand=True)
        paned_window.add(right_frame, weight=1)

        # Кнопка перевода
        translate_button = ttk.Button(main_frame, text="Перевести", command=self.do_translate)
        translate_button.pack(pady=5)

        # Статус-бар
        self.status_bar = ttk.Label(main_frame, text="Готов к работе.", relief=tk.SUNKEN, anchor="w")
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        # Вкладки для дополнительной информации
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=10)

        # Вкладка 1: Список слов
        self.tab1 = ttk.Frame(notebook)
        self.setup_tab1()
        notebook.add(self.tab1, text="Частотный список слов")

        # Вкладка 2: Синтаксическое дерево
        self.tab2 = ttk.Frame(notebook)
        self.setup_tab2()
        notebook.add(self.tab2, text="Синтаксическое дерево")

        # Меню
        self.setup_menu()

    def setup_tab1(self):
        cols = ("Слово", "Частота", "Часть речи", "Расшифровка", "Перевод")
        self.tree_words = ttk.Treeview(self.tab1, columns=cols, show="headings")
        for col in cols:
            self.tree_words.heading(col, text=col)
        self.tree_words.pack(fill=tk.BOTH, expand=True)

    def setup_tab2(self):
        ttk.Label(self.tab2, text="Выберите предложение для анализа:").pack(anchor="w", padx=5, pady=5)
        self.sentence_selector = ttk.Combobox(self.tab2, state="readonly")
        self.sentence_selector.pack(fill=tk.X, padx=5)
        self.sentence_selector.bind("<<ComboboxSelected>>", self.show_parse_tree)

        self.parse_tree_text = scrolledtext.ScrolledText(self.tab2, wrap=tk.WORD, state="disabled",
                                                         font=("Courier", 10))
        self.parse_tree_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def setup_menu(self):
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        # <<< ИЗМЕНЕНО: Добавили новый пункт меню "Открыть файл..."
        file_menu.add_command(label="Открыть файл...", command=self.open_file)
        file_menu.add_command(label="Сохранить результат", command=self.save_results)
        file_menu.add_separator()
        file_menu.add_command(label="Выход",
                              command=self.on_closing)  # <<< ИЗМЕНЕНО: Лучше вызывать наш метод on_closing
        menu_bar.add_cascade(label="Файл", menu=file_menu)

        dict_menu = tk.Menu(menu_bar, tearoff=0)
        dict_menu.add_command(label="Редактировать словарь", command=self.edit_dictionary)
        menu_bar.add_cascade(label="Словарь", menu=dict_menu)

    # <<< НОВОЕ: Метод для открытия и чтения файла
    def open_file(self):
        """Открывает диалог выбора файла и загружает текст в поле ввода."""
        filepath = filedialog.askopenfilename(
            title="Выберите текстовый файл",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if not filepath:
            # Пользователь отменил выбор файла
            return

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            # Очищаем поле ввода и вставляем содержимое файла
            self.text_in.delete("1.0", tk.END)
            self.text_in.insert("1.0", content)
            self.status_bar.config(text=f"Файл успешно загружен: {filepath}")

        except Exception as e:
            messagebox.showerror("Ошибка чтения файла", f"Не удалось прочитать файл:\n{e}")
            self.status_bar.config(text="Ошибка при загрузке файла.")

    def do_translate(self):
        # ... (этот метод остается без изменений) ...
        input_text = self.text_in.get("1.0", tk.END).strip()
        if not input_text:
            messagebox.showwarning("Внимание", "Поле для ввода текста пустое.")
            return

        try:
            self.status_bar.config(text="Идет обработка...")
            self.root.update_idletasks()  # Обновить GUI

            self.last_result = self.translator.process_text(input_text)

            # Обновление вывода
            self.text_out.config(state="normal")
            self.text_out.delete("1.0", tk.END)
            self.text_out.insert("1.0", self.last_result['translated_text'])
            self.text_out.config(state="disabled")

            # Обновление статус-бара
            status_text = f"Слов в исходном тексте: {self.last_result['total_words']}. Переведено слов: {self.last_result['total_words']}."
            self.status_bar.config(text=status_text)

            # Обновление вкладки 1
            self.update_word_list()

            # Обновление вкладки 2
            self.update_sentence_selector()

        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
            self.status_bar.config(text="Ошибка.")

    def update_word_list(self):
        for i in self.tree_words.get_children():
            self.tree_words.delete(i)
        for item in self.last_result['word_details']:
            self.tree_words.insert("", "end", values=(
                item['word'],
                item['frequency'],
                item['pos_tag'],
                item['pos_desc'],
                item['translation']
            ))

    def update_sentence_selector(self):
        # ... (этот метод остается без изменений) ...
        if self.last_result and self.last_result['spacy_doc']:
            sentences = [sent.text for sent in self.last_result['spacy_doc'].sents]
            self.sentence_selector['values'] = sentences
            if sentences:
                self.sentence_selector.current(0)
                self.show_parse_tree()

    def show_parse_tree(self, event=None):
        selected_sentence = self.sentence_selector.get()
        if not selected_sentence:
            return

        tree_str = self.translator.get_dependency_parse(selected_sentence)
        header = f"{'TOKEN':<15} {'POS':<10} {'DEPENDENCY':<15} {'HEAD'}\n"
        header += "-" * 55 + "\n"

        self.parse_tree_text.config(state="normal")
        self.parse_tree_text.delete("1.0", tk.END)
        self.parse_tree_text.insert("1.0", header + tree_str)
        self.parse_tree_text.config(state="disabled")

    def save_results(self):
        if not self.last_result:
            messagebox.showinfo("Информация", "Нет результатов для сохранения.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            title="Сохранить результат перевода"
        )
        if not filepath:
            return

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("--- РЕЗУЛЬТАТ ПЕРЕВОДА ---\n\n")
                f.write("ИСХОДНЫЙ ТЕКСТ (АНГЛИЙСКИЙ):\n")
                f.write(self.last_result['original_text'] + "\n\n")
                f.write("ПЕРЕВЕДЕННЫЙ ТЕКСТ (НЕМЕЦКИЙ):\n")
                f.write(self.last_result['translated_text'] + "\n\n")

                f.write("--- ЧАСТОТНЫЙ СПИСОК СЛОВ ---\n\n")
                f.write(f"{'Слово':<20} | {'Частота':<10} | {'Часть речи':<15} | {'Перевод'}\n")
                f.write("-" * 70 + "\n")
                for item in self.last_result['word_details']:
                    f.write(
                        f"{item['word']:<20} | {item['frequency']:<10} | {item['pos_tag']:<15} | {item['translation']}\n")

            messagebox.showinfo("Успех", f"Результаты успешно сохранены в файл:\n{filepath}")

        except Exception as e:
            messagebox.showerror("Ошибка сохранения", f"Не удалось сохранить файл: {e}")

    def edit_dictionary(self):
        editor_win = tk.Toplevel(self.root)
        editor_win.title("Редактор словаря")
        en_word = simpledialog.askstring("Ввод", "Введите английское слово:", parent=editor_win)
        if en_word:
            de_word = simpledialog.askstring("Ввод", f"Введите перевод для '{en_word}':", parent=editor_win)
            if de_word:
                self.translator.db.add_or_update_word(en_word, de_word)
                messagebox.showinfo("Успех", f"Слово '{en_word}' добавлено/обновлено в словаре.", parent=editor_win)

    def on_closing(self):
        if messagebox.askokcancel("Выход", "Вы уверены, что хотите выйти?"):
            self.translator.close_db()
            self.root.destroy()