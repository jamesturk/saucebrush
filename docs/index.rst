saucebrush |release|
====================

Overview
--------

saucebrush is a tool for writing ETL pipelines in pure python.

The basic premise of saucebrush is that you write `Recipe` that can then
be applied to data.  A `Recipe` is a pipeline consisting of `sources`,
`filters`, and `sinks`.

A `source` is a simple object that yields one data one piece at a time.
An example of a source might be a CSV file or database, it is also possible
to write your own sources.

A `filter` is a function that takes a single record and returns a modified
version of that record.  Writing a filter is as simple as writing a function
that modifies a single record in the desired way.  A fairly comprehensive
suite of common filters is also available making it possible to do common
tasks without writing any of your own filters.

An `emitter` is actually a special case `filter` that doesn't modify
the record but instead writes data out in some way.  Emitters can be hooked
in anywhere in your pipeline but are typically placed at the end to
save the results of a recipe.  Similarly to `sources` filters exist for most
common formats (CSV, various SQL dialects, etc.) and it is also possible
to write your own emitter.

Contents:

.. toctree::
   :maxdepth: 2



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

