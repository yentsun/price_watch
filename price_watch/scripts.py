import sys
import optparse
import textwrap

from pyramid.paster import bootstrap


def pack_storage():

    description = """
    Pack the ZODB storage based on environment.
    Example: pack_storage development.ini
    """
    usage = "usage: %prog config_uri"
    parser = optparse.OptionParser(
        usage=usage,
        description=textwrap.dedent(description)
        )
    options, args = parser.parse_args(sys.argv[1:])
    if not len(args) >= 1:
        print('You must provide "config_uri"')
        return 2
    config_uri = args[0]
    env = bootstrap(config_uri)
    keeper, closer = env['root'], env['closer']
    try:
        keeper.pack()
    finally:
        closer()