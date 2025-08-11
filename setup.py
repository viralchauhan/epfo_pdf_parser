from setuptools import setup, find_packages
from pathlib import Path

setup(
    name="epfoparser",
    version="1.0.4",
    description="EPFO PDF passbook parser and console display tool with active member detection",
    author="Viral Chauhan",
    license="MIT",
    long_description=Path("README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    py_modules=["epfo_parser_final", "display_epfo"],
    install_requires=[
        "pdfplumber==0.7.6",
        "tabulate",
        "colorama",
        "reportlab"
    ],
    entry_points={
        'console_scripts': [
            'epfoparser=epfo_parser_final:main_entry',
        ],
    },
    python_requires='>=3.7',
    include_package_data=True,
)
