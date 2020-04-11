from setuptools import setup, find_packages

with open("README.md") as f:
    long_description = f.read()

setup(
    name='Labphew',
    version="0.1.0",
    packages=find_packages(),
    url='https://github.com/sanlifaez/labphew',
    license='GPLv3',
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    author='Sanli Faez',
    author_email='s.faez@uu.nl',
    description='Fun with computer-controlled experiments for beginners',
    long_description=long_description,
    test_suite='testsuite.testsuite',
    entry_points={
        'console_scripts': [
            'Labphew = Labphew.start:start'
        ],
    },
    install_requires=[
        'pint',
        'pyqt5==5.10.1',
        'pyqtgraph',
        'numpy',
        'PyYAML',
        'pyserial',
    ],
)
