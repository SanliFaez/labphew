***********************
Welcome to labphew docs
***********************

.. image:: _static/labphew_logo.png
   :scale: 50 %
   :alt: labphew logo

*labphew* (lowercase) is a minimalist functioning code module and folder structure. While trying to be a standalone and
accessible module, labphew is built to teach and practice computer-controlled measurements using Python.

labphew is meant to be:
-----------------------

* out-of-the-box package, capable of communicating with specified electronic devices.
* instructive code that allows users to learn how it works and how to customize it.
* a low entry-level template for building new user-interfaces for a measurement.
* a good example of structuring lab-automation code and how to document it
* fun to play with, edit, and contribute to the code.

labphew is NOT meant to:
------------------------
* grow into a comprehensive package for controlling all sorts of devices.
* be the fastest in performing a task or push its performance to the physical limits.
* stay backward-compatible.

You can find the code of this package at `Github <https://github.com/sanlifaez/labphew>`_.
The documentation is hosted at `Read The Docs <https://readthedocs.org/projects/labphew>`_.

.. toctree::
   :maxdepth: 1
   :caption: Further in the docs:

   introduction
   installation
   howtolabphew
   walkthrough
   labphew.model
   labphew.view
   labphew.controller
   labphew.core
   labphew.logging
   examples
   devices
   customize
   contribute


Acknowledgement
===============
This project is heavily inspired by the instruction exercise written by Dr. Aquiles Carattino,
the mastermind behind Python for the Lab (PFTL).
PFTL is developed by `Uetke <https://www.uetke.com>`_.
If you want to learn more (very serious!) coding for lab automation with Python,
check the excellent `PTFL website <https://www.pythonforthelab.com/>`_ or register for a course at `Uetke <https://www.uetke.com>`_.

An earlier and more sophisticated derivation of this software, PyNTA, which uses the multiprocessing library of Python
and the distributed messaging library pyZMQ, has been explained in
`this preprint <https://www.preprints.org/manuscript/201906.0251/v1>`_ - doi: 10.20944/preprints201906.0251.v1.
`PyNTA <https://github.com/nanoepics/pynta>`_ is capable of real-time particle tracking on Megapixel
images at a 50 Hz rate.