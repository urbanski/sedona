# Installing Sedona
Installing Sedona is pretty straightforward.

## Clone the Sedona Repository:

```
git clone git@github.com:urbanski/sedona.git
```

## Install any required modules:
* python-twisted
* nose

### For Authentication Support:
* python-bcrypt

### For Encryption Support:
* pyOpenSSL

Previous Python versions (2.6) may work, however, they aren't tested and don't natively include some modules (like argparse).

## Modify the Configuration

Edit the sample configuration file (sedona.conf) included in the conf directory.

| Config Directive | Data type | Description | Value |
| ------------- |-------------|-----|-----|
| redis-host | String | The address of the Redis server that Sedona will send commands to | redis-host = localhost |
| redis-port | Integer | The port of the Redis server that Sedona will send commands to | redis-port = 6379 |
| plaintext-support | Boolean | Specifies whether or not plaintext connections will be accepted |  plaintext-support = True |
| plaintext-port | Integer | Specifies the port that Sedona will use to accept plaintext connections | plaintext-support = 6370 |