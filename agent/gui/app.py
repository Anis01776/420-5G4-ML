from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk

BASE_DIR = Path(__file__).resolve().parent
AGENT_DIR = BASE_DIR.parent
BUILD_DIR = AGENT_DIR / "build" / "python"
if str(BUILD_DIR) not in sys.path:
    sys.path.insert(0, str(BUILD_DIR))

try:
    from .controller import LibraryController
except ImportError:
    try:
        from controller import LibraryController
    except ImportError as exc:  # pragma: no cover - message destiné à l'utilisateur
        raise SystemExit(
            "Le module C++ bibliotheque_core_py est introuvable.\n"
            "Compilez-le avec :\n"
            "  cd agent\n"
            "  ../.venv/bin/python bindings/setup.py build_ext --build-lib build/python\n"
            f"\nDétail : {exc}"
        ) from exc


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

APP_TITLE = "Bibliothèque personnelle"
DEFAULT_DATA_DIR = AGENT_DIR / "data"

BACKGROUND = "#0f172a"
HEADER = "#0b1220"
CARD = "#1e293b"
CARD_ALT = "#111827"
TEXT = "#e5e7eb"
TEXT_MUTED = "#94a3b8"
ACCENT = "#2563eb"
ACCENT_HOVER = "#1d4ed8"
SUCCESS = "#22c55e"
WARNING = "#f59e0b"
ERROR = "#ef4444"


class TextFormDialog(ctk.CTkToplevel):
    """Dialogue modal simple pour les formulaires d'ajout."""

    def __init__(self, master, title: str, fields: list[tuple[str, str]], on_submit):
        super().__init__(master)
        self.title(title)
        self.resizable(False, False)
        self.on_submit = on_submit
        self.entries: dict[str, ctk.CTkEntry] = {}

        self.transient(master)
        self.grab_set()
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(18, 8))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.grid(row=1, column=0, sticky="ew", padx=20)
        form.grid_columnconfigure(1, weight=1)

        for row, (key, label) in enumerate(fields):
            ctk.CTkLabel(form, text=label).grid(
                row=row, column=0, sticky="w", padx=(0, 12), pady=6
            )
            entry = ctk.CTkEntry(form, width=280)
            entry.grid(row=row, column=1, sticky="ew", pady=6)
            self.entries[key] = entry

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.grid(row=2, column=0, sticky="e", padx=20, pady=(12, 20))
        ctk.CTkButton(
            buttons,
            text="Annuler",
            width=100,
            fg_color="transparent",
            border_width=1,
            command=self.destroy,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(buttons, text="Valider", width=100, command=self._submit).pack(
            side="left"
        )

        self.bind("<Return>", lambda _event: self._submit())
        self.bind("<Escape>", lambda _event: self.destroy())
        self.after(50, self._focus_first)
        self.after(50, self._center)

    def _focus_first(self) -> None:
        if self.entries:
            next(iter(self.entries.values())).focus_set()

    def _center(self) -> None:
        self.update_idletasks()
        master = self.master
        x = master.winfo_rootx() + (master.winfo_width() - self.winfo_width()) // 2
        y = master.winfo_rooty() + (master.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    def _submit(self) -> None:
        values = {key: entry.get() for key, entry in self.entries.items()}
        if self.on_submit(values):
            self.destroy()


class BibliothequeApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1180x760")
        self.minsize(1100, 640)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.data_dir = DEFAULT_DATA_DIR
        self.controller = LibraryController(self.data_dir)
        self.dirty = False
        self.current_tab = "books"
        self.user_choices: dict[str, str] = {}

        self._configure_tree_style()
        self._build_ui()
        self._load_initial()

    # ------------------------------------------------------------------ UI
    def _configure_tree_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Biblio.Treeview",
            background=CARD_ALT,
            fieldbackground=CARD_ALT,
            foreground=TEXT,
            rowheight=30,
            borderwidth=0,
            font=("DejaVu Sans", 10),
        )
        style.configure(
            "Biblio.Treeview.Heading",
            background="#1f2937",
            foreground=TEXT,
            relief="flat",
            font=("DejaVu Sans", 10, "bold"),
        )
        style.map(
            "Biblio.Treeview",
            background=[("selected", ACCENT)],
            foreground=[("selected", "white")],
        )

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color=HEADER, corner_radius=0, height=64)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header,
            text="Bibliothèque personnelle",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=(20, 28), pady=16)

        nav = ctk.CTkFrame(header, fg_color="transparent")
        nav.grid(row=0, column=1, sticky="w")

        self.nav_buttons: dict[str, ctk.CTkButton] = {}
        tabs = [
            ("books", "Livres", 90),
            ("users", "Utilisateurs", 120),
            ("loans", "Emprunts / Retours", 170),
            ("data", "Sauvegarde / Statistiques", 200),
        ]
        for key, label, width in tabs:
            button = ctk.CTkButton(
                nav,
                text=label,
                width=width,
                height=34,
                fg_color="transparent",
                hover_color="#1e293b",
                text_color=TEXT_MUTED,
                command=lambda name=key: self.show_tab(name),
            )
            button.pack(side="left", padx=4)
            self.nav_buttons[key] = button

        self.dirty_label = ctk.CTkLabel(
            header,
            text="À jour",
            text_color=SUCCESS,
            font=ctk.CTkFont(size=12),
        )
        self.dirty_label.grid(row=0, column=2, sticky="e", padx=20)

        content = ctk.CTkFrame(self, fg_color=BACKGROUND, corner_radius=0)
        content.grid(row=1, column=0, sticky="nsew")
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=1)

        self.views: dict[str, ctk.CTkFrame] = {}
        for key, _label, _width in tabs:
            view = ctk.CTkFrame(content, fg_color="transparent")
            view.grid(row=0, column=0, sticky="nsew")
            self.views[key] = view

        self._build_books_view(self.views["books"])
        self._build_users_view(self.views["users"])
        self._build_loans_view(self.views["loans"])
        self._build_data_view(self.views["data"])

        status = ctk.CTkFrame(self, fg_color=HEADER, corner_radius=0, height=32)
        status.grid(row=2, column=0, sticky="ew")
        status.grid_propagate(False)
        self.status_label = ctk.CTkLabel(
            status,
            text="Prêt",
            anchor="w",
            text_color=SUCCESS,
        )
        self.status_label.pack(side="left", fill="x", expand=True, padx=20)

        self.show_tab("books")

    def _make_card(self, master, row: int, column: int, **grid_kwargs) -> ctk.CTkFrame:
        card = ctk.CTkFrame(master, fg_color=CARD, corner_radius=12)
        card.grid(row=row, column=column, **grid_kwargs)
        return card

    def _build_books_view(self, parent: ctk.CTkFrame) -> None:
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        toolbar = self._make_card(
            parent, 0, 0, sticky="ew", padx=16, pady=(16, 8)
        )
        search_row = ctk.CTkFrame(toolbar, fg_color="transparent")
        search_row.pack(fill="x", padx=12, pady=(12, 6))

        self.search_entry = ctk.CTkEntry(
            search_row,
            placeholder_text="Rechercher un livre...",
            width=250,
        )
        self.search_entry.pack(side="left", padx=(0, 8))
        self.search_entry.bind("<Return>", lambda _event: self.search_books())

        self.search_mode = ctk.CTkOptionMenu(
            search_row,
            values=["Titre", "Auteur"],
            width=100,
            command=lambda _value: self.search_books(),
        )
        self.search_mode.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            search_row,
            text="Rechercher",
            width=105,
            command=self.search_books,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            search_row,
            text="Réinitialiser",
            width=110,
            fg_color="transparent",
            border_width=1,
            command=self.reset_search,
        ).pack(side="left", padx=(0, 12))

        self.books_filter = ctk.CTkSegmentedButton(
            search_row,
            values=["Tous", "Disponibles"],
            command=lambda _value: self.refresh_books(),
        )
        self.books_filter.set("Tous")
        self.books_filter.pack(side="left")

        action_row = ctk.CTkFrame(toolbar, fg_color="transparent")
        action_row.pack(fill="x", padx=12, pady=(0, 12))

        ctk.CTkButton(
            action_row, text="Ajouter un livre", width=130, command=self.add_book_dialog
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            action_row,
            text="Supprimer",
            width=100,
            fg_color="#b91c1c",
            hover_color="#991b1b",
            command=self.remove_selected_book,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            action_row, text="Emprunter", width=110, command=self.checkout_selected_book
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            action_row, text="Retourner", width=110, command=self.return_selected_book
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            action_row,
            text="Actualiser",
            width=110,
            fg_color="transparent",
            border_width=1,
            command=self.refresh_books,
        ).pack(side="left")

        self.books_count_label = ctk.CTkLabel(
            action_row, text="0 livre(s)", text_color=TEXT_MUTED
        )
        self.books_count_label.pack(side="right")

        table_frame = self._make_card(
            parent, 1, 0, sticky="nsew", padx=16, pady=(0, 16)
        )
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        columns = ("title", "author", "isbn", "status", "borrower")
        self.books_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            style="Biblio.Treeview",
            selectmode="browse",
        )
        headings = [
            ("title", "Titre", 260, "w"),
            ("author", "Auteur", 190, "w"),
            ("isbn", "ISBN", 150, "w"),
            ("status", "Statut", 150, "w"),
            ("borrower", "Emprunteur", 110, "w"),
        ]
        for column, label, width, anchor in headings:
            self.books_tree.heading(column, text=label)
            self.books_tree.column(column, width=width, anchor=anchor, stretch=True)
        self.books_tree.tag_configure("available", foreground="#4ade80")
        self.books_tree.tag_configure("borrowed", foreground="#fbbf24")
        self.books_tree.grid(row=0, column=0, sticky="nsew", padx=(12, 0), pady=12)

        scrollbar = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.books_tree.yview
        )
        self.books_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 12), pady=12)

    def _build_users_view(self, parent: ctk.CTkFrame) -> None:
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        toolbar = self._make_card(
            parent, 0, 0, sticky="ew", padx=16, pady=(16, 8)
        )
        ctk.CTkButton(
            toolbar,
            text="Ajouter un utilisateur",
            width=170,
            command=self.add_user_dialog,
        ).pack(side="left", padx=12, pady=12)
        ctk.CTkButton(
            toolbar,
            text="Actualiser",
            width=110,
            fg_color="transparent",
            border_width=1,
            command=self.refresh_users,
        ).pack(side="left", padx=(0, 12), pady=12)
        self.users_count_label = ctk.CTkLabel(
            toolbar, text="0 utilisateur(s)", text_color=TEXT_MUTED
        )
        self.users_count_label.pack(side="right", padx=12)

        table_frame = self._make_card(
            parent, 1, 0, sticky="nsew", padx=16, pady=(0, 16)
        )
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        columns = ("name", "user_id", "count", "books")
        self.users_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            style="Biblio.Treeview",
            selectmode="browse",
        )
        headings = [
            ("name", "Nom", 260, "w"),
            ("user_id", "Identifiant", 160, "w"),
            ("count", "Emprunts", 100, "center"),
            ("books", "ISBN empruntés", 380, "w"),
        ]
        for column, label, width, anchor in headings:
            self.users_tree.heading(column, text=label)
            self.users_tree.column(column, width=width, anchor=anchor, stretch=True)
        self.users_tree.grid(row=0, column=0, sticky="nsew", padx=(12, 0), pady=12)

        scrollbar = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.users_tree.yview
        )
        self.users_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 12), pady=12)

    def _build_loans_view(self, parent: ctk.CTkFrame) -> None:
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        cards = ctk.CTkFrame(parent, fg_color="transparent")
        cards.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        cards.grid_columnconfigure(0, weight=1)
        cards.grid_columnconfigure(1, weight=1)

        checkout_card = self._make_card(
            cards, 0, 0, sticky="nsew", padx=(0, 8)
        )
        ctk.CTkLabel(
            checkout_card,
            text="Emprunter un livre",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(14, 8))

        checkout_form = ctk.CTkFrame(checkout_card, fg_color="transparent")
        checkout_form.pack(fill="x", padx=16)
        checkout_form.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(checkout_form, text="ISBN").grid(
            row=0, column=0, sticky="w", padx=(0, 12), pady=6
        )
        self.loan_isbn_entry = ctk.CTkEntry(checkout_form)
        self.loan_isbn_entry.grid(row=0, column=1, sticky="ew", pady=6)

        ctk.CTkLabel(checkout_form, text="Utilisateur").grid(
            row=1, column=0, sticky="w", padx=(0, 12), pady=6
        )
        self.loan_user_menu = ctk.CTkOptionMenu(
            checkout_form, values=["Aucun utilisateur"], width=240
        )
        self.loan_user_menu.grid(row=1, column=1, sticky="ew", pady=6)

        ctk.CTkButton(
            checkout_card,
            text="Emprunter",
            width=130,
            command=self.checkout_from_loans,
        ).pack(anchor="w", padx=16, pady=(10, 16))

        return_card = self._make_card(
            cards, 0, 1, sticky="nsew", padx=(8, 0)
        )
        ctk.CTkLabel(
            return_card,
            text="Retourner un livre",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(14, 8))

        return_form = ctk.CTkFrame(return_card, fg_color="transparent")
        return_form.pack(fill="x", padx=16)
        return_form.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(return_form, text="ISBN").grid(
            row=0, column=0, sticky="w", padx=(0, 12), pady=6
        )
        self.return_isbn_entry = ctk.CTkEntry(return_form)
        self.return_isbn_entry.grid(row=0, column=1, sticky="ew", pady=6)

        ctk.CTkButton(
            return_card,
            text="Retourner",
            width=130,
            fg_color="#b45309",
            hover_color="#92400e",
            command=self.return_from_loans,
        ).pack(anchor="w", padx=16, pady=(18, 16))

        table_card = self._make_card(
            parent, 1, 0, sticky="nsew", padx=16, pady=(0, 16)
        )
        table_card.grid_rowconfigure(1, weight=1)
        table_card.grid_columnconfigure(0, weight=1)

        table_header = ctk.CTkFrame(table_card, fg_color="transparent")
        table_header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=12, pady=(12, 0))
        ctk.CTkLabel(
            table_header,
            text="Livres actuellement empruntés",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left")
        self.loans_count_label = ctk.CTkLabel(
            table_header, text="0 emprunt(s)", text_color=TEXT_MUTED
        )
        self.loans_count_label.pack(side="right")

        columns = ("title", "author", "isbn", "borrower")
        self.loans_tree = ttk.Treeview(
            table_card,
            columns=columns,
            show="headings",
            style="Biblio.Treeview",
            selectmode="browse",
        )
        headings = [
            ("title", "Titre", 280, "w"),
            ("author", "Auteur", 190, "w"),
            ("isbn", "ISBN", 160, "w"),
            ("borrower", "Emprunteur", 130, "w"),
        ]
        for column, label, width, anchor in headings:
            self.loans_tree.heading(column, text=label)
            self.loans_tree.column(column, width=width, anchor=anchor, stretch=True)
        self.loans_tree.grid(row=1, column=0, sticky="nsew", padx=(12, 0), pady=12)
        self.loans_tree.bind("<<TreeviewSelect>>", self.on_loan_selected)

        scrollbar = ttk.Scrollbar(
            table_card, orient="vertical", command=self.loans_tree.yview
        )
        self.loans_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=1, column=1, sticky="ns", padx=(0, 12), pady=12)

    def _build_data_view(self, parent: ctk.CTkFrame) -> None:
        parent.grid_rowconfigure(2, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        stats = ctk.CTkFrame(parent, fg_color="transparent")
        stats.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        for column in range(4):
            stats.grid_columnconfigure(column, weight=1)

        cards = [
            ("total_books", "Total livres"),
            ("available_books", "Disponibles"),
            ("checked_out_books", "Empruntés"),
            ("total_users", "Utilisateurs"),
        ]
        self.stat_labels: dict[str, ctk.CTkLabel] = {}
        for index, (key, label) in enumerate(cards):
            card = self._make_card(
                stats,
                0,
                index,
                sticky="nsew",
                padx=(0 if index == 0 else 8, 0),
            )
            ctk.CTkLabel(card, text=label, text_color=TEXT_MUTED).pack(
                anchor="w", padx=16, pady=(14, 0)
            )
            value = ctk.CTkLabel(
                card,
                text="0",
                font=ctk.CTkFont(size=28, weight="bold"),
            )
            value.pack(anchor="w", padx=16, pady=(0, 14))
            self.stat_labels[key] = value

        data_card = self._make_card(
            parent, 1, 0, sticky="ew", padx=16, pady=8
        )
        data_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            data_card,
            text="Répertoire de données",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 4))

        self.data_dir_label = ctk.CTkLabel(
            data_card,
            text=str(self.data_dir),
            text_color=TEXT_MUTED,
            anchor="w",
        )
        self.data_dir_label.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 10))

        buttons = ctk.CTkFrame(data_card, fg_color="transparent")
        buttons.grid(row=2, column=0, sticky="w", padx=16, pady=(0, 14))
        ctk.CTkButton(
            buttons,
            text="Choisir un répertoire",
            width=160,
            fg_color="transparent",
            border_width=1,
            command=self.choose_data_dir,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            buttons,
            text="Sauvegarder",
            width=130,
            command=lambda: self.save(confirm=True),
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            buttons,
            text="Créer une sauvegarde",
            width=170,
            fg_color="#0f766e",
            hover_color="#115e59",
            command=self.create_backup,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            buttons,
            text="Recharger",
            width=110,
            fg_color="transparent",
            border_width=1,
            command=self.reload_data,
        ).pack(side="left")

        log_card = self._make_card(
            parent, 2, 0, sticky="nsew", padx=16, pady=(8, 16)
        )
        log_card.grid_rowconfigure(1, weight=1)
        log_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            log_card,
            text="Journal des actions",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(12, 4))
        self.activity_text = ctk.CTkTextbox(
            log_card,
            height=140,
            corner_radius=8,
            fg_color=CARD_ALT,
            text_color=TEXT,
        )
        self.activity_text.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.activity_text.configure(state="disabled")

    # --------------------------------------------------------------- appels
    def _load_initial(self) -> None:
        ok, message = self.controller.load()
        self.set_status(message, not ok)
        self.refresh_all()

    def show_tab(self, name: str) -> None:
        if name not in self.views:
            return
        self.current_tab = name
        self.views[name].tkraise()
        for key, button in self.nav_buttons.items():
            active = key == name
            button.configure(
                fg_color=ACCENT if active else "transparent",
                text_color="white" if active else TEXT_MUTED,
            )

        if name == "books":
            self.refresh_books()
        elif name == "users":
            self.refresh_users()
        elif name == "loans":
            self.refresh_loans()
            self.refresh_loan_user_menu()
        elif name == "data":
            self.refresh_statistics()

    def refresh_all(self) -> None:
        self.refresh_books()
        self.refresh_users()
        self.refresh_loan_user_menu()
        self.refresh_loans()
        self.refresh_statistics()
        self._update_dirty_indicator()

    def refresh_books(self) -> None:
        query = self.search_entry.get().strip()
        mode = self.search_mode.get()
        try:
            if query:
                if mode == "Auteur":
                    books = self.controller.search_books_by_author(query)
                else:
                    books = self.controller.search_books_by_title(query)
            else:
                books = self.controller.get_all_books()
            if self.books_filter.get() == "Disponibles":
                books = [book for book in books if book.available]
        except Exception as exc:
            self.set_status(f"Impossible de charger les livres : {exc}", True)
            return

        self._clear_tree(self.books_tree)
        for book in books:
            status = "Disponible" if book.available else f"Emprunté ({book.borrower_id})"
            tag = "available" if book.available else "borrowed"
            self.books_tree.insert(
                "",
                "end",
                iid=book.isbn,
                values=(book.title, book.author, book.isbn, status, book.borrower_id),
                tags=(tag,),
            )
        self.books_count_label.configure(text=f"{len(books)} livre(s)")

    def refresh_users(self) -> None:
        try:
            users = self.controller.get_all_users()
        except Exception as exc:
            self.set_status(f"Impossible de charger les utilisateurs : {exc}", True)
            return

        self._clear_tree(self.users_tree)
        for user in users:
            borrowed = ", ".join(user.borrowed_books) if user.borrowed_books else "—"
            self.users_tree.insert(
                "",
                "end",
                iid=user.user_id,
                values=(user.name, user.user_id, len(user.borrowed_books), borrowed),
            )
        self.users_count_label.configure(text=f"{len(users)} utilisateur(s)")

    def refresh_loans(self) -> None:
        try:
            books = self.controller.get_borrowed_books()
        except Exception as exc:
            self.set_status(f"Impossible de charger les emprunts : {exc}", True)
            return

        self._clear_tree(self.loans_tree)
        for book in books:
            self.loans_tree.insert(
                "",
                "end",
                iid=book.isbn,
                values=(book.title, book.author, book.isbn, book.borrower_id),
            )
        self.loans_count_label.configure(text=f"{len(books)} emprunt(s)")

    def refresh_loan_user_menu(self) -> None:
        try:
            users = self.controller.get_all_users()
        except Exception as exc:
            self.set_status(f"Impossible de charger les utilisateurs : {exc}", True)
            return
        self.user_choices = {
            f"{user.user_id} — {user.name}": user.user_id for user in users
        }
        values = list(self.user_choices) or ["Aucun utilisateur"]
        self.loan_user_menu.configure(values=values)
        if self.loan_user_menu.get() not in values:
            self.loan_user_menu.set(values[0])

    def refresh_statistics(self) -> None:
        try:
            stats = self.controller.get_statistics()
        except Exception as exc:
            self.set_status(f"Impossible de charger les statistiques : {exc}", True)
            return
        for key, label in self.stat_labels.items():
            label.configure(text=str(stats.get(key, 0)))

    # ------------------------------------------------------------- actions
    def search_books(self) -> None:
        self.refresh_books()

    def reset_search(self) -> None:
        self.search_entry.delete(0, "end")
        self.search_mode.set("Titre")
        self.books_filter.set("Tous")
        self.refresh_books()

    def add_book_dialog(self) -> None:
        TextFormDialog(
            self,
            "Ajouter un livre",
            [("title", "Titre"), ("author", "Auteur"), ("isbn", "ISBN")],
            self.submit_book,
        )

    def submit_book(self, values: dict[str, str]) -> bool:
        ok, message = self.controller.add_book(
            values["title"], values["author"], values["isbn"]
        )
        self.set_status(message, not ok)
        if ok:
            self.mark_dirty()
            self.refresh_all()
        return ok

    def add_user_dialog(self) -> None:
        TextFormDialog(
            self,
            "Ajouter un utilisateur",
            [("name", "Nom"), ("user_id", "Identifiant")],
            self.submit_user,
        )

    def submit_user(self, values: dict[str, str]) -> bool:
        ok, message = self.controller.add_user(values["name"], values["user_id"])
        self.set_status(message, not ok)
        if ok:
            self.mark_dirty()
            self.refresh_all()
        return ok

    def remove_selected_book(self) -> None:
        isbn = self._selected_isbn(self.books_tree)
        if isbn is None:
            messagebox.showinfo(
                "Aucun livre sélectionné",
                "Sélectionnez un livre dans le tableau.",
                parent=self,
            )
            return
        book = self.controller.find_book(isbn)
        if book is None:
            self.set_status("Livre introuvable.", True)
            return
        if not book.available:
            if not messagebox.askyesno(
                "Livre emprunté",
                "Ce livre est actuellement emprunté. Le supprimer quand même ?",
                parent=self,
            ):
                return
        if not messagebox.askyesno(
            "Supprimer le livre",
            f"Supprimer « {book.title} » ?",
            parent=self,
        ):
            return
        ok, message = self.controller.remove_book(isbn)
        self.set_status(message, not ok)
        if ok:
            self.mark_dirty()
            self.refresh_all()

    def checkout_selected_book(self) -> None:
        isbn = self._selected_isbn(self.books_tree)
        if isbn is None:
            messagebox.showinfo(
                "Aucun livre sélectionné",
                "Sélectionnez un livre dans le tableau.",
                parent=self,
            )
            return
        self._start_checkout(isbn)

    def _start_checkout(self, isbn: str) -> None:
        self.loan_isbn_entry.delete(0, "end")
        self.loan_isbn_entry.insert(0, isbn)
        self.show_tab("loans")
        self.loan_user_menu.focus_set()
        self.set_status(f"Livre {isbn} sélectionné. Choisissez un utilisateur.")

    def return_selected_book(self) -> None:
        isbn = self._selected_isbn(self.books_tree)
        if isbn is None:
            messagebox.showinfo(
                "Aucun livre sélectionné",
                "Sélectionnez un livre dans le tableau.",
                parent=self,
            )
            return
        book = self.controller.find_book(isbn)
        if book is None:
            self.set_status("Livre introuvable.", True)
            return
        if book.available:
            self.set_status("Ce livre est déjà disponible.")
            return
        if not messagebox.askyesno(
            "Retourner le livre",
            f"Retourner « {book.title} » ?",
            parent=self,
        ):
            return
        ok, message = self.controller.return_book(isbn)
        self.set_status(message, not ok)
        if ok:
            self.mark_dirty()
            self.refresh_all()

    def on_loan_selected(self, _event=None) -> None:
        isbn = self._selected_isbn(self.loans_tree)
        if isbn is not None:
            self.return_isbn_entry.delete(0, "end")
            self.return_isbn_entry.insert(0, isbn)

    def checkout_from_loans(self) -> None:
        isbn = self.loan_isbn_entry.get().strip()
        display = self.loan_user_menu.get()
        user_id = self.user_choices.get(display)
        if user_id is None:
            self.set_status("Sélectionnez un utilisateur.", True)
            return
        ok, message = self.controller.check_out_book(isbn, user_id)
        self.set_status(message, not ok)
        if ok:
            self.mark_dirty()
            self.loan_isbn_entry.delete(0, "end")
            self.refresh_all()

    def return_from_loans(self) -> None:
        isbn = self.return_isbn_entry.get().strip()
        ok, message = self.controller.return_book(isbn)
        self.set_status(message, not ok)
        if ok:
            self.mark_dirty()
            self.return_isbn_entry.delete(0, "end")
            self.refresh_all()

    def choose_data_dir(self) -> None:
        if self.dirty:
            answer = messagebox.askyesnocancel(
                "Changer de répertoire",
                "Des modifications ne sont pas sauvegardées. "
                "Voulez-vous les sauvegarder avant de changer de répertoire ?",
                parent=self,
            )
            if answer is None:
                return
            if answer and not self.save(confirm=False):
                return

        directory = filedialog.askdirectory(
            initialdir=str(self.data_dir), parent=self
        )
        if not directory:
            return

        new_controller = LibraryController(Path(directory))
        ok, message = new_controller.load()
        if not ok:
            messagebox.showerror("Répertoire invalide", message, parent=self)
            return

        self.controller = new_controller
        self.data_dir = new_controller.data_dir
        self.data_dir_label.configure(text=str(self.data_dir))
        self.dirty = False
        self.refresh_all()
        self.set_status(message)

    def reload_data(self) -> None:
        if self.dirty:
            answer = messagebox.askyesnocancel(
                "Recharger les données",
                "Des modifications ne sont pas sauvegardées. "
                "Voulez-vous les sauvegarder avant de recharger ?",
                parent=self,
            )
            if answer is None:
                return
            if answer and not self.save(confirm=False):
                return

        new_controller = LibraryController(self.data_dir)
        ok, message = new_controller.load()
        if not ok:
            messagebox.showerror("Rechargement impossible", message, parent=self)
            return
        self.controller = new_controller
        self.dirty = False
        self.refresh_all()
        self.set_status(message)

    def save(self, confirm: bool = True) -> bool:
        if not self.dirty:
            self.set_status("Aucune modification à sauvegarder.")
            return True
        if confirm and not messagebox.askyesno(
            "Sauvegarder",
            "Sauvegarder les modifications dans les fichiers de données ?",
            parent=self,
        ):
            return False
        ok, message = self.controller.save()
        self.set_status(message, not ok)
        if ok:
            self.dirty = False
            self._update_dirty_indicator()
        return ok

    def create_backup(self) -> None:
        if not messagebox.askyesno(
            "Créer une sauvegarde",
            "Créer une copie .backup des fichiers books.txt et users.txt ?\n\n"
            "Les modifications non sauvegardées ne seront pas incluses.",
            parent=self,
        ):
            return
        ok, message = self.controller.create_backup()
        self.set_status(message, not ok)
        if not ok:
            messagebox.showerror(
                "Sauvegarde impossible",
                message
                + "\n\nSi des fichiers .backup existent déjà, supprimez-les "
                "manuellement avant de réessayer.",
                parent=self,
            )

    def on_close(self) -> None:
        if self.dirty:
            answer = messagebox.askyesnocancel(
                "Quitter",
                "Des modifications ne sont pas sauvegardées. "
                "Voulez-vous sauvegarder avant de quitter ?",
                parent=self,
            )
            if answer is None:
                return
            if answer and not self.save(confirm=False):
                return
        self.destroy()

    # ------------------------------------------------------------- helpers
    def mark_dirty(self) -> None:
        self.dirty = True
        self._update_dirty_indicator()

    def _update_dirty_indicator(self) -> None:
        if self.dirty:
            self.dirty_label.configure(
                text="● Modifications non sauvegardées", text_color=WARNING
            )
        else:
            self.dirty_label.configure(text="À jour", text_color=SUCCESS)

    def set_status(self, message: str, error: bool = False) -> None:
        self.status_label.configure(
            text=message, text_color=ERROR if error else SUCCESS
        )
        self._log(("ERREUR : " if error else "") + message)

    def _log(self, message: str) -> None:
        if not hasattr(self, "activity_text"):
            return
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.activity_text.configure(state="normal")
        self.activity_text.insert("end", f"[{timestamp}] {message}\n")
        self.activity_text.see("end")
        self.activity_text.configure(state="disabled")

    @staticmethod
    def _clear_tree(tree: ttk.Treeview) -> None:
        for item in tree.get_children():
            tree.delete(item)

    @staticmethod
    def _selected_isbn(tree: ttk.Treeview) -> str | None:
        selection = tree.selection()
        if not selection:
            return None
        return selection[0]


if __name__ == "__main__":
    app = BibliothequeApp()
    app.mainloop()
