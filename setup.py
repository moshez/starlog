import setuptools

#with open("README.rst") as fp:
#    long_description = fp.read()
long_description = ""

setuptools.setup(
    name="starlog",
    license="MIT",
    description="",
    long_description=long_description,
    use_incremental=True,
    setup_requires=["incremental"],
    author="Moshe Zadka",
    author_email="moshez@zadka.club",
    packages=setuptools.find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=["incremental", "ipywidgets"],
    extras_require=dict(
        test=["virtue", "pyhamcrest", "coverage"],
        lint=["black", "flake8", "mypy"],
        doc=["sphinx"],
    ),
    entry_points=dict(
        console_scripts=["starlog=starlog.runpy:run"],
    ),
)
