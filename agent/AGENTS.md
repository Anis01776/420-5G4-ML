# AGENTS.md — Bibliothèque C++

`agent/` is a C++17 library manager with a French CLI and a Python CustomTkinter GUI. The CLI requires CMake >= 3.21 and no external libraries; the GUI uses pybind11 and CustomTkinter. The VS Code dev container is optional.

## Build and run

```bash
cd agent
cmake -S . -B build
cmake --build build
./build/bibliotheque -d data
```

- `CMakeLists.txt` uses `file(GLOB SOURCES "*.cpp")`: rerun `cmake -S . -B build` after adding or removing a `.cpp`, otherwise the change is not compiled.
- `-d/--data-dir` is required for persistence. Without it, the file names are empty, loads report missing data, and saves fail. Run from `agent/` with `-d data`.
- No tests, linter, formatter, or CI. Verify by compiling (warnings `-Wall -Wextra -Wpedantic` are already enabled) and exercising the CLI.

## GUI (Python + pybind11)

The existing C++ sources and `CMakeLists.txt` are intentionally untouched by the GUI. The module is built independently from `bindings/setup.py`:

```bash
cd agent
../.venv/bin/python -m pip install -r gui/requirements.txt
../.venv/bin/python bindings/setup.py build_ext \
  --build-lib build/python \
  --build-temp build/pybind11-tmp
../.venv/bin/python gui/app.py
```

- `bindings/bindings.cpp` is the only C++ binding file. It exposes `Book`, `User`, `Library`, and `FileManager`; pointer-returning methods are wrapped to return copies.
- `gui/controller.py` holds the Python-side validation and error messages. `gui/app.py` is the CustomTkinter UI with four tabs: Livres, Utilisateurs, Emprunts / Retours, Sauvegarde / Statistiques.
- Building the module requires Python development headers (`python3-dev` on Debian/Ubuntu, `python3-devel` on Fedora) and `pybind11` from `gui/requirements.txt`.
- The GUI rebuilds `build/python/` with `setup.py`; it does not use the CMake build targets.

## Layout

- `main.cpp`: argument parsing and interactive menu loop.
- `library.*`: owns `Book`/`User` objects via `unique_ptr`; accessors return non-owning raw pointers, so do not delete them.
- `book.*`, `user.*`: models and pipe-delimited serialization.
- `filemanager.*`: loads/saves the whole `books.txt` and `users.txt` files; also creates backups.
- `bindings/`: pybind11 module and its standalone `setup.py`.
- `gui/`: CustomTkinter application, Python controller, and GUI requirements.

## Data and testing gotchas

- `data/books.txt` and `data/users.txt` are tracked fixtures. Both CLI and GUI rewrite them on save; test mutations on a copy (`cp -r data /tmp/biblio-test`) and restore with `git checkout -- data`.
- File formats: books are `title|author|isbn|1/0|borrowerId`; users are `name|userId|isbn1,isbn2`.
- Every menu action ends with `pauseForInput()`, which consumes two Enter presses. When piping stdin, add an extra blank line per pause, e.g. `printf '5\n\n\n0\n' | ./build/bibliotheque -d /tmp/biblio-test`.
- Menu 13 (`Créer une Sauvegarde`) aborts on a second run because existing `*.backup` files are not overwritten. The GUI does not fix this: it catches the error and asks the user to delete the `.backup` files manually.
- `build/` is gitignored; do not commit binaries or build artifacts.

Keep user-facing strings, comments, and existing identifiers in French.
