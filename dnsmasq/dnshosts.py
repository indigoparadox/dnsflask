
import re

def combine_host_reservations( hosts, reservations ):
    return map(
        lambda x: {
            # IP4 if present, otherwise IP6.
            'ip': x['ip4'] if 'ip4' in x else x['ip6'] if 'ip6' in x else None,
            'mac':
                # Grab reservation for this host.
                [r for s in map(
                    lambda y: y['mac'],
                    filter( lambda z: 
                        z['ip4'] == x['ip4'] if 'ip4' in x and 'ip4' in z else 
                        z['ip6'] == x['ip6'] if 'ip6' in x and 'ip6' in z else
                        None,
                        reservations
                    )
                ) for r in s],
            'name': x['name']
        },
        hosts
    )

def read_hosts( path='/etc/hosts' ):
    re_host = re.compile( '((?P<ip4>[0-9]*\\.[0-9]*\\.[0-9]*\\.[0-9]*)|(?P<ip6>[0-9a-fA-F:]*))\\s*(?P<name>[a-zA-Z0-9\\-_]*)' )
    hosts = []
    with open( path, 'r' ) as hosts_file:
        for line in hosts_file:
            host_match = re_host.match( line )
            if host_match:
                hosts += [host_match.groupdict()]
    return hosts

