# Interface graphique

L'interface est écrite en Python avec CustomTkinter. Elle utilise le module
C++ `bibliotheque_core_py`, compilé avec pybind11.

## Dépendances système

- Python avec Tkinter (`python3-tk` sur Debian/Ubuntu).
- Les en-têtes de développement Python pour compiler le binding
  (`python3-dev` sur Debian/Ubuntu, `python3-devel` sur Fedora).
- Un compilateur C++17 et CMake ne sont pas nécessaires pour le binding :
  il est compilé directement par `setup.py`.

## Installation des dépendances Python

Depuis la racine du dépôt :

```bash
.venv/bin/python -m pip install -r agent/gui/requirements.txt
```

## Compilation du binding

Depuis `agent/` :

```bash
../.venv/bin/python bindings/setup.py build_ext \
  --build-lib build/python \
  --build-temp build/pybind11-tmp
```

Le module est produit dans `agent/build/python/`. `app.py` ajoute
automatiquement ce répertoire à `sys.path`.

## Lancement

Toujours depuis `agent/` :

```bash
../.venv/bin/python gui/app.py
```

## Remarques

- Le CLI existant et les sources C++ existantes ne sont pas modifiés.
- Le backend est le binding minimal `bindings/bindings.cpp`.
- Le bug de `FileManager::createBackup()` est conservé : si des fichiers
  `.backup` existent déjà, l'UI affiche l'erreur et demande de les supprimer
  manuellement.
- Pour changer de répertoire de données, utiliser l'onglet
  « Sauvegarde / Statistiques ».
