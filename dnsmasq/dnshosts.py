
import re

def combine_host_reservations( hosts, reservations ):
    return map(
        lambda x: {
            # IP4 if present, otherwise IP6.
            'ip': x['ip'] if 'ip' in x else None,
            'mac':
                # Grab reservation for this host.
                [r for s in map(
                    lambda y: y['mac'],
                    filter( lambda z: 
                        z['ip'] == x['ip'] if 'ip' in x and 'ip' in z else 
                        None,
                        reservations
                    )
                ) for r in s],
            'name': x['name'],
            'key': x['ip'].replace( '.', '' ) if 'ip' in x else None
        },
        hosts
    )

def read_hosts( path ):
    re_host = re.compile( '(?P<ip>[0-9:.]*)\\s*(?P<name>[a-zA-Z0-9\\-_]*)' )
    hosts = []
    with open( path, 'r' ) as hosts_file:
        for line in hosts_file:
            host_match = re_host.match( line )
            if host_match:
                hosts += [host_match.groupdict()]
    return hosts

