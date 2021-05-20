from collections import namedtuple

import camus
from unittest import mock

from pytest import raises


IdRecord = namedtuple("IdRecord", "id")


def check_id(i, row):
    assert row.id == i


class MockAurora:
    def begin_transaction(**kwargs):
        pass

    def commit_transaction(**kwargs):
        pass

    def rollback_transaction(**kwargs):
        pass

    def execute_transaction(**kwargs):
        pass


class TestRecordCollection:
    def test_iter(self):
        rows = camus.RecordCollection(IdRecord(i) for i in range(10))
        for i, row in enumerate(rows):
            check_id(i, row)

    def test_next(self):
        rows = camus.RecordCollection(IdRecord(i) for i in range(10))
        for i in range(10):
            check_id(i, next(rows))

    def test_iter_and_next(self):
        rows = camus.RecordCollection(IdRecord(i) for i in range(10))
        i = enumerate(iter(rows))
        check_id(*next(i))  # Cache first row.
        next(rows)  # Cache second row.
        check_id(*next(i))  # Read second row from cache.

    def test_multiple_iter(self):
        rows = camus.RecordCollection(IdRecord(i) for i in range(10))
        i = enumerate(iter(rows))
        j = enumerate(iter(rows))

        check_id(*next(i))  # Cache first row.

        check_id(*next(j))  # Read first row from cache.
        check_id(*next(j))  # Cache second row.

        check_id(*next(i))  # Read second row from cache.

    def test_slice_iter(self):
        rows = camus.RecordCollection(IdRecord(i) for i in range(10))
        for i, row in enumerate(rows[:5]):
            check_id(i, row)
        for i, row in enumerate(rows):
            check_id(i, row)
        assert len(rows) == 10

    # all
    def test_all_returns_a_list_of_records(self):
        rows = camus.RecordCollection(IdRecord(i) for i in range(3))
        assert rows.all() == [IdRecord(0), IdRecord(1), IdRecord(2)]

    # first
    def test_first_returns_a_single_record(self):
        rows = camus.RecordCollection(IdRecord(i) for i in range(1))
        assert rows.first() == IdRecord(0)

    def test_first_defaults_to_None(self):
        rows = camus.RecordCollection(iter([]))
        assert rows.first() is None

    def test_first_default_is_overridable(self):
        rows = camus.RecordCollection(iter([]))
        assert rows.first("Cheese") == "Cheese"

    def test_first_raises_default_if_its_an_exception_subclass(self):
        rows = camus.RecordCollection(iter([]))

        class Cheese(Exception):
            pass

        raises(Cheese, rows.first, Cheese)

    def test_first_raises_default_if_its_an_exception_instance(self):
        rows = camus.RecordCollection(iter([]))

        class Cheese(Exception):
            pass

        raises(Cheese, rows.first, Cheese("cheddar"))

    # one
    def test_one_returns_a_single_record(self):
        rows = camus.RecordCollection(IdRecord(i) for i in range(1))
        assert rows.one() == IdRecord(0)

    def test_one_defaults_to_None(self):
        rows = camus.RecordCollection(iter([]))
        assert rows.one() is None

    def test_one_default_is_overridable(self):
        rows = camus.RecordCollection(iter([]))
        assert rows.one("Cheese") == "Cheese"

    def test_one_raises_when_more_than_one(self):
        rows = camus.RecordCollection(IdRecord(i) for i in range(3))
        raises(ValueError, rows.one)

    def test_one_raises_default_if_its_an_exception_subclass(self):
        rows = camus.RecordCollection(iter([]))

        class Cheese(Exception):
            pass

        raises(Cheese, rows.one, Cheese)

    def test_one_raises_default_if_its_an_exception_instance(self):
        rows = camus.RecordCollection(iter([]))

        class Cheese(Exception):
            pass

        raises(Cheese, rows.one, Cheese("cheddar"))

    # scalar
    def test_scalar_returns_a_single_record(self):
        rows = camus.RecordCollection(IdRecord(i) for i in range(1))
        assert rows.scalar() == 0

    def test_scalar_defaults_to_None(self):
        rows = camus.RecordCollection(iter([]))
        assert rows.scalar() is None

    def test_scalar_default_is_overridable(self):
        rows = camus.RecordCollection(iter([]))
        assert rows.scalar("Kaffe") == "Kaffe"

    def test_scalar_raises_when_more_than_one(self):
        rows = camus.RecordCollection(IdRecord(i) for i in range(3))
        raises(ValueError, rows.scalar)


class TestRecord:
    def test_record_dir(self):
        keys, values = ["id", "name", "email"], [1, "", ""]
        record = camus.Record(keys, values)
        _dir = dir(record)
        for key in keys:
            assert key in _dir
        for key in dir(object):
            assert key in _dir

    def test_record_duplicate_column(self):
        keys, values = ["id", "name", "email", "email"], [1, "", "", ""]
        record = camus.Record(keys, values)
        with raises(KeyError):
            record["email"]

@mock.patch("camus.boto3")
class TestTransaction:
    def test_raise(self, boto3):
        payload = {
            "secret_arn": 'arn:aws:secretsmanager:us-east-1:123456789012:secret:your-secret-name-ByH87J',
            "resource_arn": 'arn:aws:rds:us-east-1:123456789012:cluster:your-cluster-name',
            "dbname": 'testing'
        }

        aurora = MockAurora()

        db = camus.Database(**payload, conn=aurora)

        with db.transaction() as txid:
            db.query("SELECT * FROM teste")

