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

Edit the sample configuration files included in the conf directory.