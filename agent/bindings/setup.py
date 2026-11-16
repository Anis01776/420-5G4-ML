from pathlib import Path

from setuptools import setup
from pybind11.setup_helpers import Pybind11Extension, build_ext

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

extension = Pybind11Extension(
    "bibliotheque_core_py",
    sources=[
        str(HERE / "bindings.cpp"),
        str(ROOT / "book.cpp"),
        str(ROOT / "user.cpp"),
        str(ROOT / "library.cpp"),
        str(ROOT / "filemanager.cpp"),
    ],
    include_dirs=[str(ROOT)],
    cxx_std=17,
    extra_compile_args=["-Wall", "-Wextra"],
)

setup(
    name="bibliotheque-core-py",
    version="0.1.0",
    description="Binding pybind11 minimal pour l'interface graphique de la bibliotheque",
    ext_modules=[extension],
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
)
