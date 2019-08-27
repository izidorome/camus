# Camus
**Camus is a raw SQL library enabling an ease integration with the new [Aurora Serverless Data API]("https://aws.amazon.com/blogs/aws/new-data-api-for-amazon-aurora-serverless/"). It is a fork of the powerful [Records]("https://github.com/kennethreitz/records") library.**

![Camus Aurora Execution](https://raw.githubusercontent.com/rizidoro/camus/master/camus.png)
## Instalation

The recommended installation method is `pipenv`:

```shell
$ pipenv install camus
```

## Basic Usage

First you need to have an Aurora cluster ARN and a Secret ARN. If don't have one yet, just follow the [Data API Getting Started Guide]("https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/data-api.html").

With that in hands, let's drop some query to our database:

```python
import camus

db = camus.Database(
    resource_arn="arn:aws:rds:us-east-1:123456789012:cluster:your-cluster-name",
    secret_arn="arn:aws:secretsmanager:us-east-1:123456789012:secret:your-secret-name-ByH87J",
    dbname="mydb",
)

rows = db.query("SELECT * FROM users")
```

You can grab one row at time (like in Records library)

```python
>>> rows[0]
<camus.Record at 0x109bfbd30>
```

Or iterate over them:

```python
 for r in rows:
     print(r.name, r.email)
```

Like mentioned before, Camus is a fork of the Records library, so almost all access pattern are equal:

```python
  row.email
  row['email']
  row[3]
```

Other options include `rows.as_dict()` and `rows.as_dict(ordered=True)`


## Transactions

Data API transactions are supported by Camus:

```python
with db.transaction() as txid:
    db.query("INSERT INTO users (name, email) VALUES (:name, :email)", name="Rafael", email="rafael@email.com")
    db.query("UPDATE posts SET title = :title WHERE id = :id", title="New Title", id=999)
```

If any exception is raised when executing any of the queries, a rollback is performed automatically.

## That's all folks
Thanks for the awesome @kennethreitz for providing his knowledge on the excelent Records library and
all the talks he has given over the years!
