from setuptools import setup, find_packages

setup(
    name="epfoparser",
    version="1.0.0",
    description="EPFO PDF passbook parser and console display tool",
    author="Your Name",
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
