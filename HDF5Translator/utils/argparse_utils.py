import argparse

# for handling the optional keyval arguments for feeding additional parameters to your operation
class KeyValueAction(argparse.Action):
    """
    Custom action for argparse to parse key-value pairs from the command line.
    """

    def __call__(self, parser, namespace, values, option_string=None):
        keyvals = {}
        for item in values:
            # Split on the first equals sign
            key, value = item.split("=", 1)
            keyvals[key.strip()] = value.strip()
        setattr(namespace, self.dest, keyvals)
