from inspect import isclass
from collections import OrderedDict
from contextlib import contextmanager

import boto3

aurora = boto3.client("rds-data")


def isexception(obj):
    """Given an object, return a boolean indicating whether it is an instance
    or subclass of :py:class:`Exception`.
    """
    if isinstance(obj, Exception):
        return True
    if isclass(obj) and issubclass(obj, Exception):
        return True
    return False


class RecordCollection(object):
    def __init__(self, rows):
        self._rows = rows
        self._all_rows = []
        self.pending = True

    def __repr__(self):
        return "<RecordCollection size={} pending={}>".format(len(self), self.pending)

    def __iter__(self):
        i = 0
        while True:
            if i < len(self):
                yield self[i]
            else:
                try:
                    yield next(self)
                except StopIteration:
                    return
            i += 1

    def next(self):
        return self.__next__()

    def __next__(self):
        try:
            nextrow = next(self._rows)
            self._all_rows.append(nextrow)
            return nextrow
        except StopIteration:
            self.pending = False
            raise StopIteration("RecordCollection contains no more rows.")

    def __getitem__(self, key):
        is_int = isinstance(key, int)

        # Convert RecordCollection[1] into slice.
        if is_int:
            key = slice(key, key + 1)

        while len(self) < key.stop or key.stop is None:
            try:
                next(self)
            except StopIteration:
                break

        rows = self._all_rows[key]
        if is_int:
            return rows[0]
        else:
            return RecordCollection(iter(rows))

    def __len__(self):
        return len(self._all_rows)

    def all(self, as_dict=False, as_ordereddict=False):
        """Returns a list of all rows for the RecordCollection. If they haven't
        been fetched yet, consume the iterator and cache the results."""

        # By calling list it calls the __iter__ method
        rows = list(self)

        if as_dict:
            return [r.as_dict() for r in rows]
        elif as_ordereddict:
            return [r.as_dict(ordered=True) for r in rows]

        return rows

    def as_dict(self, ordered=False):
        return self.all(as_dict=not (ordered), as_ordereddict=ordered)

    def first(self, default=None, as_dict=False, as_ordereddict=False):
        """Returns a single record for the RecordCollection, or `default`. If
        `default` is an instance or subclass of Exception, then raise it
        instead of returning it."""

        # Try to get a record, or return/raise default.
        try:
            record = self[0]
        except IndexError:
            if isexception(default):
                raise default
            return default

        # Cast and return.
        if as_dict:
            return record.as_dict()
        elif as_ordereddict:
            return record.as_dict(ordered=True)
        else:
            return record

    def one(self, default=None, as_dict=False, as_ordereddict=False):
        """Returns a single record for the RecordCollection, ensuring that it
        is the only record, or returns `default`. If `default` is an instance
        or subclass of Exception, then raise it instead of returning it."""

        # Ensure that we don't have more than one row.
        try:
            self[1]
        except IndexError:
            return self.first(
                default=default, as_dict=as_dict, as_ordereddict=as_ordereddict
            )
        else:
            raise ValueError(
                "RecordCollection contained more than one row. "
                "Expects only one row when using "
                "RecordCollection.one"
            )

    def scalar(self, default=None):
        """Returns the first column of the first row, or `default`."""
        row = self.one()
        return row[0] if row else default


class Record(object):
    """A row, from a query, from a database."""

    __slots__ = ("_keys", "_values")

    def __init__(self, keys, values):
        self._keys = keys
        self._values = values

        # Ensure that lengths match properly.
        assert len(self._keys) == len(self._values)

    def keys(self):
        """Returns the list of column names from the query."""
        return self._keys

    def values(self):
        """Returns the list of values from the query."""
        return self._values

    def __getitem__(self, key):
        # Support for index-based lookup.
        if isinstance(key, int):
            return self.values()[key]

        # Support for string-based lookup.
        if key in self.keys():
            i = self.keys().index(key)
            if self.keys().count(key) > 1:
                raise KeyError("Record contains multiple '{}' fields.".format(key))
            return self.values()[i]

        raise KeyError("Record contains no '{}' field.".format(key))

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as e:
            raise AttributeError(e)

    def __dir__(self):
        standard = dir(super(Record, self))
        # Merge standard attrs with generated ones (from column names).
        return sorted(standard + [str(k) for k in self.keys()])

    def get(self, key, default=None):
        """Returns the value for a given key, or default."""
        try:
            return self[key]
        except KeyError:
            return default

    def as_dict(self, ordered=False):
        """Returns the row as a dictionary, as ordered."""
        items = zip(self.keys(), self.values())

        return OrderedDict(items) if ordered else dict(items)


class Database:
    def __init__(self, secret_arn, resource_arn, dbname):
        self._secret_arn = secret_arn
        self._resource_arn = resource_arn
        self._dbname = dbname
        self._transactionId = None

    def _auth(self):
        return {
            "secretArn": self._secret_arn,
            "resourceArn": self._resource_arn,
        }

    @contextmanager
    def transaction(self):
        """A context manager for executing a transaction on this Database."""
        tx = aurora.begin_transaction(**self._auth(), database=self._dbname)
        self._transactionId = tx['transactionId']

        try:
            yield self._transactionId
            aurora.commit_transaction(**self._auth(), transactionId=self._transactionId)
        except:
            aurora.rollback_transaction(**self._auth(), transactionId=tx['transactionId'])
        finally:
            self._transactionId = None

    def query(self, sql, fetchall=False, **params):
        attrs = {
            **self._auth(),
            "database": self._dbname,
            "sql": f"{sql}",
            "includeResultMetadata": True,
        }

        if params:
            attrs["parameters"] = self._build_parameters(**params)

        if self._transactionId:
            attrs["transactionId"] = self._transactionId

        result = aurora.execute_statement(**attrs)

        if "records" in result:
            columns = [meta["label"] for meta in result["columnMetadata"]]
            values = [self._fetch_value(r) for r in result["records"]]

            row_gen = (Record(columns, row) for row in values)

            records = RecordCollection(row_gen)

            if fetchall:
                records.all()
        else:
            record = Record(["records_updated"], [result["numberOfRecordsUpdated"]])
            records = RecordCollection(iter([record]))

        return records

    def _fetch_value(self, record):
        values = [value[0] for value in [list(field.values()) for field in record]]

        # transform isNull to None
        keys = [key[0] for key in [list(field.keys()) for field in record]]

        for idx, key in enumerate(keys):
            if key == 'isNull':
                values[idx] = None

        return values

    def _build_parameters(self, **params):
        params = [self._build_field(field, value) for field, value in params.items()]
        return params

    def _build_field(self, field, value):
        fieldtype = type(value).__name__

        typemap = {
            "str": "stringValue",
            "int": "longValue",
            "bool": "booleanValue",
            "float": "doubleValue",
            "NoneType": "isNull"
        }

        if fieldtype == "NoneType":
            value = True

        return {"name": field, "value": {typemap[fieldtype]: value}}
