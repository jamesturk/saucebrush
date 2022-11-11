from contextlib import closing
from io import StringIO
import os

from saucebrush.emitters import (
    DebugEmitter,
    CSVEmitter,
    CountEmitter,
    SqliteEmitter,
    SqlDumpEmitter,
)


def test_debug_emitter():
    with closing(StringIO()) as output:
        de = DebugEmitter(output)
        list(de.attach([1, 2, 3]))
        assert output.getvalue() == "1\n2\n3\n"


def test_count_emitter():

    # values for test
    values = [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
    ]

    with closing(StringIO()) as output:

        # test without of parameter
        ce = CountEmitter(every=10, outfile=output, format="%(count)s records\n")
        list(ce.attach(values))
        assert output.getvalue() == "10 records\n20 records\n"
        ce.done()
        assert output.getvalue() == "10 records\n20 records\n22 records\n"

    with closing(StringIO()) as output:

        # test with of parameter
        ce = CountEmitter(every=10, outfile=output, of=len(values))
        list(ce.attach(values))
        assert output.getvalue() == "10 of 22\n20 of 22\n"
        ce.done()
        assert output.getvalue() == "10 of 22\n20 of 22\n22 of 22\n"


def test_csv_emitter():
    io = StringIO()  # if Python 3.x then use StringIO

    with closing(io) as output:
        ce = CSVEmitter(output, ("x", "y", "z"))
        list(ce.attach([{"x": 1, "y": 2, "z": 3}, {"x": 5, "y": 5, "z": 5}]))
        assert output.getvalue() == "x,y,z\r\n1,2,3\r\n5,5,5\r\n"


def test_sqlite_emitter():

    import sqlite3
    import tempfile

    with closing(tempfile.NamedTemporaryFile(suffix=".db")) as f:
        db_path = f.name

    sle = SqliteEmitter(db_path, "testtable", fieldnames=("a", "b", "c"))
    list(sle.attach([{"a": "1", "b": "2", "c": "3"}]))
    sle.done()

    with closing(sqlite3.connect(db_path)) as conn:
        cur = conn.cursor()
        cur.execute("""SELECT a, b, c FROM testtable""")
        results = cur.fetchall()

    os.unlink(db_path)

    assert results == [("1", "2", "3")]


def test_sql_dump_emitter():

    with closing(StringIO()) as bffr:

        sde = SqlDumpEmitter(bffr, "testtable", ("a", "b"))
        list(sde.attach([{"a": 1, "b": "2"}]))
        sde.done()

        assert bffr.getvalue() == "INSERT INTO `testtable` (`a`,`b`) VALUES (1,'2');\n"
