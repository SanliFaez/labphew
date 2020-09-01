***********
V for view
***********
All the files related to the GUI should be placed within the View package. This is the third leg of the
MVC design pattern. If the Model is properly built, the Views are relatively simple PyQt objects. It is
important to point out that if there is any logic of the experiment that goes into the view, the code is
going to become harder to share, unless it is for the exact same purpose.

The real-time plots are built on `pyQtGraph http://www.pyqtgraph.org/`,
a GUI library that gives access to a powerful set of tools for embedding plots in user interfaces.

The icons used in the GUI are designed by The Artificial\footnote{https://toicon.com} and released under a CC-BY license.

The view is one of the most challenging aspects of any program,
since it requires a different set of skills compared to the rest of the program.
Building the view on top of a well-defined model makes it also independent from it.
By completely separating the logic of the experiment and the devices from the view itself,
it is possible to quickly prototype solutions that in most cases are enough for a researcher.

Essential methods
-----------------

..
    .. automodule:: PythonForTheLab.view.scan_window
       :members:
       :undoc-members:
       :show-inheritance:

    .. automodule:: PythonForTheLab.View.monitor_window
       :members:
       :undoc-members:
       :show-inheritance:

    .. automodule:: PythonForTheLab.View.config_window
       :members:
       :undoc-members:
       :show-inheritance:


    .. automodule:: PythonForTheLab.View.general_worker
       :members:
       :undoc-members:
       :show-inheritance:
