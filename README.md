# uptest

_A small utility to send requests to servers and notify by email if an error occured._

## Usage

```
./uptest.py
```

## Configuration

You need to configure your mailer as well as the sites you want to check, in a `config.py` file. An example file is
available:

```python3
mailer = {
    "username": "contact@example.com",
    "password": "mypassword",
    "host": "smtp.example.com",
    "port": "465",
    "dest": "contact@example.com",
}

urls = [
    "example.com",
    "example.com/toto",
]
```
