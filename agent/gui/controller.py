from __future__ import annotations

from pathlib import Path

import bibliotheque_core_py as core


class LibraryController:
    """Petite couche Python autour du binding C++ minimal."""

    def __init__(self, data_dir: str | Path) -> None:
        self.data_dir = Path(data_dir).expanduser().resolve()
        self.library = core.Library()
        self.file_manager = core.FileManager(
            str(self.data_dir / "books.txt"),
            str(self.data_dir / "users.txt"),
        )
        self.loaded = False

    def load(self) -> tuple[bool, str]:
        if self.loaded:
            return True, "Les données sont déjà chargées."
        if not self.data_dir.is_dir():
            return False, f"Le répertoire de données n'existe pas : {self.data_dir}"

        try:
            self.file_manager.load_library_data(self.library)
        except Exception as exc:
            return False, f"Impossible de charger les données : {exc}"

        self.loaded = True
        books = self.library.get_total_books()
        users = len(self.library.get_all_users())
        return True, f"Chargé {books} livre(s) et {users} utilisateur(s)."

    def save(self) -> tuple[bool, str]:
        if not self.loaded:
            return False, "Les données ne sont pas chargées."
        try:
            saved = self.file_manager.save_library_data(self.library)
        except Exception as exc:
            return False, f"Impossible de sauvegarder les données : {exc}"
        if not saved:
            return False, "Impossible de sauvegarder les données."
        return True, "Données sauvegardées avec succès."

    def create_backup(self) -> tuple[bool, str]:
        if not self.loaded:
            return False, "Les données ne sont pas chargées."

        books_file = self.data_dir / "books.txt"
        users_file = self.data_dir / "users.txt"
        if not books_file.exists() and not users_file.exists():
            return False, "Aucun fichier de données à sauvegarder."

        try:
            self.file_manager.create_backup()
        except RuntimeError as exc:
            return False, f"Échec de la sauvegarde : {exc}"
        except Exception as exc:
            return False, f"Échec de la sauvegarde : {exc}"
        return True, "Sauvegarde créée avec succès."

    def add_book(self, title: str, author: str, isbn: str) -> tuple[bool, str]:
        title = title.strip()
        author = author.strip()
        isbn = isbn.strip()
        if not title or not author or not isbn:
            return False, "Le titre, l'auteur et l'ISBN sont obligatoires."
        try:
            if self.library.find_book_by_isbn(isbn) is not None:
                return False, f"Un livre avec l'ISBN {isbn} existe déjà."
            self.library.add_book(core.Book(title, author, isbn))
        except Exception as exc:
            return False, f"Impossible d'ajouter le livre : {exc}"
        return True, "Livre ajouté avec succès."

    def remove_book(self, isbn: str) -> tuple[bool, str]:
        isbn = isbn.strip()
        if not isbn:
            return False, "L'ISBN est obligatoire."
        try:
            if not self.library.remove_book(isbn):
                return False, f"Aucun livre trouvé avec l'ISBN {isbn}."
        except Exception as exc:
            return False, f"Impossible de supprimer le livre : {exc}"
        return True, "Livre supprimé avec succès."

    def search_books_by_title(self, title: str) -> list[core.Book]:
        query = title.strip()
        if not query:
            return self.get_all_books()
        return list(self.library.search_books_by_title(query))

    def search_books_by_author(self, author: str) -> list[core.Book]:
        query = author.strip()
        if not query:
            return self.get_all_books()
        return list(self.library.search_books_by_author(query))

    def get_all_books(self) -> list[core.Book]:
        return list(self.library.get_all_books())

    def get_available_books(self) -> list[core.Book]:
        return list(self.library.get_available_books())

    def find_book(self, isbn: str) -> core.Book | None:
        return self.library.find_book_by_isbn(isbn.strip())

    def add_user(self, name: str, user_id: str) -> tuple[bool, str]:
        name = name.strip()
        user_id = user_id.strip()
        if not name or not user_id:
            return False, "Le nom et l'identifiant sont obligatoires."
        try:
            if self.library.find_user_by_id(user_id) is not None:
                return False, f"Un utilisateur avec l'identifiant {user_id} existe déjà."
            self.library.add_user(core.User(name, user_id))
        except Exception as exc:
            return False, f"Impossible d'ajouter l'utilisateur : {exc}"
        return True, "Utilisateur ajouté avec succès."

    def get_all_users(self) -> list[core.User]:
        return list(self.library.get_all_users())

    def find_user(self, user_id: str) -> core.User | None:
        return self.library.find_user_by_id(user_id.strip())

    def check_out_book(self, isbn: str, user_id: str) -> tuple[bool, str]:
        isbn = isbn.strip()
        user_id = user_id.strip()
        if not isbn or not user_id:
            return False, "L'ISBN et l'identifiant utilisateur sont obligatoires."

        book = self.find_book(isbn)
        if book is None:
            return False, f"Aucun livre trouvé avec l'ISBN {isbn}."
        user = self.find_user(user_id)
        if user is None:
            return False, f"Aucun utilisateur trouvé avec l'identifiant {user_id}."
        if not book.available:
            return False, "Ce livre est déjà emprunté."

        try:
            if not self.library.check_out_book(isbn, user_id):
                return False, "Impossible d'emprunter ce livre."
        except Exception as exc:
            return False, f"Impossible d'emprunter ce livre : {exc}"
        return True, "Livre emprunté avec succès."

    def return_book(self, isbn: str) -> tuple[bool, str]:
        isbn = isbn.strip()
        if not isbn:
            return False, "L'ISBN est obligatoire."

        book = self.find_book(isbn)
        if book is None:
            return False, f"Aucun livre trouvé avec l'ISBN {isbn}."
        if book.available:
            return False, "Ce livre est déjà disponible."

        try:
            if not self.library.return_book(isbn):
                return False, "Impossible de retourner ce livre."
        except Exception as exc:
            return False, f"Impossible de retourner ce livre : {exc}"
        return True, "Livre retourné avec succès."

    def get_borrowed_books(self) -> list[core.Book]:
        return [book for book in self.get_all_books() if not book.available]

    def get_statistics(self) -> dict[str, int]:
        return {
            "total_books": self.library.get_total_books(),
            "available_books": self.library.get_available_book_count(),
            "checked_out_books": self.library.get_checked_out_book_count(),
            "total_users": len(self.library.get_all_users()),
        }
