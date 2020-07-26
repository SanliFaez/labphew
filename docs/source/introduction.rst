***********************
Introduction to labphew
***********************

Python is a very popular programming language among scientists. It comes with a strong user community and many
well maintained computation packages. While using the Python computational and data-visualisation tools
is now common in many research groups, not so many packages have been developed for interfacing to hardware for
general use. Several research groups who have developed their Python code for their particular experiments have
shared those codes or even published them as articles. Parts of these codes can be adjusted to run a different
experiment. Quite often, this adjustments require low-level programming, which increases the barrier for building
on top of those codes, or contributing back in a mutually benefitial way.

We have started the labphew project to fill in the educational gap in using Python for instrumentation,
and at the same time to provide a minimal package that works for simple experiments, and hopeful can be extended
as it gathers more users.


labphew strategic choices
-------------------------

In order to stay focused on the main goals of the labphew project, and do not get distracted by
feature-creep, a few strategic choices have been made:

    1. labphew is mainly a functioning template for educating beginners
    2. users are encouraged to freely edit the code **but** preserve the folder structure
    3. the scope of the labphew project is limited to controlling only two devices: a camera and a data acquisition card
    4. *controllers* of the sister packages should be made rather easy to import (see :doc:`./labphew.controller`)
    5. labphew is not meant to be a support package for other code and backward compatibility is unnecessary
    6. writing a new applications usually begins with writing a new *model* (see :doc:`./labphew.model`)
    7. working with labphew should be fun and convenient

Where to start?
---------------

There is unique good path to browse these docs. If you want to learn more about the how the labphew modules,
how about taking :doc:`walkthrough`.

glossary of terms:
------------------

classes and building blocks
^^^^^^^^^^^^^^^^^^^^^^^^^^^

    + ``Operator``: Class containing group operations necessary for a measurement ("Experiment" in PFTL)
    + An operation: each function in the ``Operator`` class
    + ``MonitorWindow``: Class containing the GUI and interactions for monitoring operations that run continuously
    + ``ScanWindow``: Class containing the GUI and update inquiries for one-time operations that can be called from another window or command line
    + ``WorkThread``: Class wrapping a PyQt QThread. Called to perform certain operations in a separate thread (e.g. to avoid locking the GUI).

folders structure
^^^^^^^^^^^^^^^^^

    + adapt : folder containing python routines from other packages that are in progress of being imported
    + attic : folder containing old versions that might be deleted before each major release

reserved phrases
^^^^^^^^^^^^^^^^

    + blink_* : files in the program hierarchy that can be used to guide beginners
    + _blank_* : skeleton of files that can be used to develop a new driver or model, almost from scratch

