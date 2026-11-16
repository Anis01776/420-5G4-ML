#include <optional>
#include <string>
#include <vector>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "book.h"
#include "filemanager.h"
#include "library.h"
#include "user.h"

namespace py = pybind11;

namespace {

std::vector<Book> copyBooks(const std::vector<Book*>& books) {
    std::vector<Book> result;
    result.reserve(books.size());
    for (const Book* book : books) {
        result.push_back(*book);
    }
    return result;
}

std::vector<User> copyUsers(const std::vector<User*>& users) {
    std::vector<User> result;
    result.reserve(users.size());
    for (const User* user : users) {
        result.push_back(*user);
    }
    return result;
}

std::optional<Book> findBook(Library& library, const std::string& isbn) {
    Book* book = library.findBookByISBN(isbn);
    if (book == nullptr) {
        return std::nullopt;
    }
    return *book;
}

std::optional<User> findUser(Library& library, const std::string& userId) {
    User* user = library.findUserById(userId);
    if (user == nullptr) {
        return std::nullopt;
    }
    return *user;
}

} // namespace

PYBIND11_MODULE(bibliotheque_core_py, module) {
    module.doc() = "Binding pybind11 minimal pour l'interface graphique.";

    py::class_<Book>(module, "Book")
        .def(py::init<>())
        .def(py::init<const std::string&, const std::string&, const std::string&>(),
             py::arg("title"),
             py::arg("author"),
             py::arg("isbn"))
        .def_property_readonly("title", &Book::getTitle)
        .def_property_readonly("author", &Book::getAuthor)
        .def_property_readonly("isbn", &Book::getISBN)
        .def_property_readonly("available", &Book::getAvailability)
        .def_property_readonly("borrower_id", &Book::getBorrowerId)
        .def("to_string", &Book::toString);

    py::class_<User>(module, "User")
        .def(py::init<>())
        .def(py::init<const std::string&, const std::string&>(),
             py::arg("name"),
             py::arg("user_id"))
        .def_property_readonly("name", &User::getName)
        .def_property_readonly("user_id", &User::getUserId)
        .def_property_readonly("borrowed_books", &User::getBorrowedBooks)
        .def("to_string", &User::toString);

    py::class_<Library>(module, "Library")
        .def(py::init<>())
        .def("add_book", &Library::addBook, py::arg("book"))
        .def("remove_book", &Library::removeBook, py::arg("isbn"))
        .def("find_book_by_isbn", &findBook, py::arg("isbn"))
        .def("search_books_by_title",
             [](Library& library, const std::string& title) {
                 return copyBooks(library.searchBooksByTitle(title));
             },
             py::arg("title"))
        .def("search_books_by_author",
             [](Library& library, const std::string& author) {
                 return copyBooks(library.searchBooksByAuthor(author));
             },
             py::arg("author"))
        .def("get_available_books",
             [](Library& library) { return copyBooks(library.getAvailableBooks()); })
        .def("get_all_books",
             [](Library& library) { return copyBooks(library.getAllBooks()); })
        .def("add_user", &Library::addUser, py::arg("user"))
        .def("find_user_by_id", &findUser, py::arg("user_id"))
        .def("get_all_users",
             [](Library& library) { return copyUsers(library.getAllUsers()); })
        .def("check_out_book",
             &Library::checkOutBook,
             py::arg("isbn"),
             py::arg("user_id"))
        .def("return_book", &Library::returnBook, py::arg("isbn"))
        .def("get_total_books", &Library::getTotalBooks)
        .def("get_available_book_count", &Library::getAvailableBookCount)
        .def("get_checked_out_book_count", &Library::getCheckedOutBookCount);

    py::class_<FileManager>(module, "FileManager")
        .def(py::init<const std::string&, const std::string&>(),
             py::arg("books_file"),
             py::arg("users_file"))
        .def("load_library_data", &FileManager::loadLibraryData, py::arg("library"))
        .def("save_library_data", &FileManager::saveLibraryData, py::arg("library"))
        .def("create_backup", &FileManager::createBackup)
        .def("file_exists", &FileManager::fileExists, py::arg("filename"));
}
