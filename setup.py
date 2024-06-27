# pylint: skip-file
import re

from setuptools import setup


def get_property(prop):
    result = re.search(
        rf'{prop}\s*=\s*[\'"]([^\'"]*)[\'"]',
        open("ipyoverlay/__init__.py").read(),
    )
    return result.group(1)


with open("README.md", encoding="utf-8") as infile:
    long_description = infile.read()


setup(
    name="ipyoverlay",
    version=get_property("__version__"),
    description="IPyWidget wrappers to support rendering widgets on top of other widgets",
    keywords=["widget", "details-on-demand", "overlay", "ipywidget", "jupyter"],
    long_description_content_type="text/markdown",
    long_description=long_description,
    author="Nathan Martindale, Jacob Smith, Jason Hite, Scott L. Stewart, Mark Adams, Lisa Linville",
    author_email="ipyoverlay-help@ornl.gov",
    python_requires=">=3.9",
    url="https://github.com/ORNL/ipyoverlay",
    project_urls={
        "Documentation": "https://ornl.github.io/ipyoverlay/latest/index.html"
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Science/Research",
    ],
    packages=["ipyoverlay"],
    package_data={"ipyoverlay": ["vue/*"]},
    include_package_data=True,
    install_requires=[
        "ipyvuetify",
        "ipywidgets",
        "matplotlib",  # make optional
        "plotly",  # make optional
    ],
    # extras_require={"h5": ["tables"]},
)
