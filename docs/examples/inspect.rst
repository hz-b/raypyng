06 inspect demo
***************

This example extracts one beamline-elements table from the RML file and writes
it to CSV and XLSX. The same checked-in CSV snapshot is rendered below as an
HTML table.

.. literalinclude:: ../../examples/06_inspect_demo/example_inspect.py
   :language: python

Rendered table:

.. csv-table::
   :file: ../../examples/06_inspect_demo/inspect_output/tables/beamline_elements_table.csv
   :header-rows: 1
