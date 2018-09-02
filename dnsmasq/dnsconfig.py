
import re

DEFAULT_CONFIG_PATH='/etc/dnsmasq.conf'
EMPTY_OPTIONS = ['expand-hosts', 'stop-dns-rebind', 'rebind-localhost-ok', 'dhcp-authoritative', 'enable-ra']
RE_RESERVATION = re.compile( '(?P<disabled>#)?dhcp-host=(?P<mac>[0-9a-zA-Z:,]*),(?P<ip4>[0-9]*\\.[0-9]*\\.[0-9]*\\.[0-9]*)' )
RE_SERVER = re.compile( '(?P<disabled>#)?server=\\/(?P<domain>[a-zA-Z0-9.\\-_]*)\\/(?P<address>[0-9]*\\.[0-9]*\\.[0-9]*\\.[0-9]*)(#(?P<dest_port>[0-9]*))?(@(?P<interface>[a-zA-Z0-9.\\-_]*)(#(?P<src_port>[0-9]*))?)?' )
RE_INTERFACE = re.compile( '(?P<disabled>#)?interface=(?P<interface>[a-zA-Z0-9]*)' )
RE_CNAME = re.compile( '(?P<disabled>#)?cname=(?P<source>[a-zA-Z0-9.\\-_]*),(?P<dest>[a-zA-Z0-9.\\-_]*)' )
RE_OPTIONS = re.compile( '(?P<disabled>#)?(?P<option>domain|resolv-file|dhcp-hostsfile|pid-file|expand-hosts|min-port|stop-dns-rebind|rebind-localhost-ok|dhcp-lease-max|dhcp-authoritative|enable-ra)(=(?P<value>.*))?' )

def parse_lines( pattern, path=DEFAULT_CONFIG_PATH ):
    res_list = []
    with open( path, 'r' ) as config_file:
        for line in config_file:
            match = pattern.match( line )
            if match:
                res_list += [match.groupdict()]
    return res_list

def merge_update( list_in, key_in, update_in ):
    list_out = []
    found = False
    for item in list_in:
        if item[key_in] == update_in[key_in]:
            # This was the item requested, so edit it.
            for key, val in item.items():
                if key == key_in or key not in update_in:
                    continue
                item[key] = update_in[key]
            found = True
        list_out += [item]

    if not found:
        # We didn't perform any edits, so this must be a new item.
        list_out += [update_in]

    return list_out

def read_config( path=DEFAULT_CONFIG_PATH, exclude=[] ):
    new_config = []
    with open( path, 'r' ) as config_file:
        for line in config_file:
            exclude_line = False
            for pattern in exclude:
                match = pattern.match( line )
                if match:
                    exclude_line = True
            if not exclude_line:
                new_config += [line.strip()]

    return new_config

