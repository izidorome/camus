import boto3
from .record import Record, RecordCollection

aurora = boto3.client("rds-data")


class Database:
    def __init__(self, secret_arn, resource_arn, dbname):
        self._secret_arn = secret_arn
        self._resource_arn = resource_arn
        self._dbname = dbname

    def query(self, sql, fetchall=False, **params):
        attrs = {
            "secretArn": self._secret_arn,
            "database": self._dbname,
            "resourceArn": self._resource_arn,
            "sql": f"{sql}",
            "includeResultMetadata": True,
        }

        if params:
            attrs["parameters"] = self._build_parameters(**params)

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
        }

        return {"name": field, "value": {typemap[fieldtype]: value}}
