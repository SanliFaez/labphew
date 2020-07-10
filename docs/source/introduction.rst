***********************
Introduction to labphew
***********************

:todo: why did we create labphew?

labphew strategic choices
-------------------------

In order to stay focused on the main goals of the labphew project, and do not get distracted by
feature-creep, a few strategic choices have been made:

    1. labphew is mainly a functioning template for educating beginners
    2. users are encouraged to edit the code **but** preserve the folder structure
    3. the scope of the labphew project is limited to controlling only two devices: a camera and a data acquisition card
    4. controllers of the sister packages should be made rather easy to import
    5. labphew is not meant to be a support package for other code and backward compatibility is unnecessary
    6. writing new applications start from writing a new [model](./labphew.model.rst)
    7. working with labphew should be fun and convenient

standard operations
-------------------

:todo: explain how should one start the program and what to expect

glossary of terms:
------------------

classes and building blocks
^^^^^^^^^^^^^^^^^^^^^^^^^^^

    * Operator: Class containing group operations necessary for a measurement ("Experiment" in PFTL)
    * operation: each function in the Operator class
    * MonitorWindow: Class containing the GUI and interactions for monitoring operations that run continuously
    * ScanWindow: Class containing the GUI and update inquiries for one-time operations that can be called from another window or command line
    * WorkThread: same as WorkThread in PFTL

folders structure
^^^^^^^^^^^^^^^^^
    * adapt : folder containing python routines from other packages that are in progress of importing
    * attic : folder containing old versions that can be deleted before each release

reserved filenames
^^^^^^^^^^^^^^^^^^

    * blink : files in the program hierarchy that can be used to guide beginners
    * _blank : skeleton of files that can be used to develop a new driver or model


useful python resources
-----------------------