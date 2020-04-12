# Welcome to Labphew documentation!
==============================================
![Labphew logo](lapphew_logo.png)

*Labphew* is a starters minimalist code and folder structure for developing a computer-controlled experiment in Python. The main purpose of Labphew is to provide a basis for those with little coding experience to build their own user-interface for a piece of hardware or to control a measurement. 


### Python for the Lab
-------------
This project is heavily inspired by the instruction exercise written by [Dr. Aquiles Carattino](https://www.uetke.com), the mastermind behind [Python for the Lab](https://www.pythonforthelab.com/). If you want to learn more (serious!) coding for lab automation with Python, check the excellent [PTFL website](https://www.pythonforthelab.com/) or book him for a course.

Python for the Lab (PFTL) is a code architecture and a programming course for computer-controlled instrumentation. PTFL codes are designed following the MVC design pattern, splitting the code into Controllers for defining drivers, Models for specifying the logic of the experiment, and View for parking the GUI.
PFTL was developed by [Uetke](https://www.uetke.com) to explain to researchers, through simple examples, what can be achieved quickly with little programming experience. The ultimate goal of this project is to serve as a reference place for people interested in instrumentation written in Python.

You can find the code of the original exercise at [Github](https://github.com/PFTL/SimpleDaq/), the documentation is hosted at [Read The Docs](https://readthedocs.org/projects/python-for-the-lab/). If you are interested in learning more about Python For The Lab, you can check [Uetke's courses](https://uetke.com/courses/).

## The Labphew package
-------------
Currently, the labphew package contains more wishes than executable pieces. However you can use its framework as a (hopefully convenient) starting point to write your own code. Please note that this package is published under [GNU General Public License v3.0](https://choosealicense.com/licenses/gpl-3.0/).

However, labphew comes with a couple of modules that actually work
### Hello world with mouse clicks

### practic with external hardware: an Arduino 
The objective of PFTL is to control a device to measure the IV curve of an LED. The device is built on an Arduino DUE which has two Digital-to-Analog channels. The program monitors the voltage across a resistance while increasing the voltage applied to an LED. We can change all the parameters of the scan, including the input and output channels, the range, time delay, etc.

## Documentation
-------------
Documentation of labphew should be instructive, especially for the beginners. This is generally more difficult than writing an executable code and therefore will be done in the second phase of the project. 

The original PTFL documentation can be found at [Read the Docs](http://python-for-the-lab.readthedocs.io/en/latest/)

## How to contribute
-------------
The labphew roadmap is still incomplete. If your interests are aligned with the main purpose of this project and you want to get involved, you can send a few lines to Sanli.