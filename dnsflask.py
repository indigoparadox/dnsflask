#!/usr/bin/python

from flask import Flask, render_template, request
app = Flask( __name__ )

from dnsmasq import dnshosts, dnsconfig

CONFIG_PATH='/root/dnsmasq/dnsmasq.conf'

@app.route( '/servers' )
def route_servers():
    servers = dnsconfig.parse_lines( dnsconfig.RE_SERVER, CONFIG_PATH )
    return render_template( 'servers.html', servers=servers )

@app.route( '/cnames' )
def route_cnames():
    cnames = dnsconfig.parse_lines( dnsconfig.RE_CNAME, CONFIG_PATH )
    return render_template( 'cnames.html', cnames=cnames )

@app.route( '/cnames/save', methods=['POST'] )
def route_cnames_save():
    # Build the edit object.
    new_cname = {}
    new_cname['source'] = request.form.get( 'source' )
    new_cname['dest'] = request.form.get( 'dest' )

    # Merge updates with existing records and convert them to config lines.
    cnames = dnsconfig.parse_lines( dnsconfig.RE_CNAME, CONFIG_PATH )
    cnames = dnsconfig.merge_update( cnames, 'source', new_cname )
    cname_lines = []
    for cname in cnames:
        line = 'cname={},{}'.format( cname['source'], cname['dest'] )
        if cname['disabled']:
            line = '#' + line
        cname_lines += [line]

    # Load the existing config and apply the changes.
    new_conf = dnsconfig.read_config( CONFIG_PATH, [dnsconfig.RE_CNAME] )
    new_conf += cname_lines

    return '\n'.join( new_conf )

@app.route( '/interfaces' )
def route_interfaces():
    interfaces = dnsconfig.parse_lines( dnsconfig.RE_INTERFACE, CONFIG_PATH )
    return render_template( 'interfaces.html', interfaces=interfaces )

@app.route( '/hosts' )
def route_hosts():
    dns_hosts = dnshosts.read_hosts( '/root/dnsmasq/dnsmasq/hosts/hosts' )
    dns_res = dnsconfig.parse_lines( dnsconfig.RE_RESERVATION, CONFIG_PATH )
    dns_res_multimac = []
    for res in dns_res:
        res['mac'] = res['mac'].split( ',' )
        dns_res_multimac += [res]
    combined = dnshosts.combine_host_reservations( dns_hosts, dns_res_multimac )
    print combined
    return render_template( 'hosts.html', hosts=combined )

@app.route( '/' )
def route_root():
    options = dnsconfig.parse_lines( dnsconfig.RE_OPTIONS, CONFIG_PATH )
    return render_template(
        'index.html', options=options, empty_options=dnsconfig.EMPTY_OPTIONS )

if '__main__' == __name__:
	app.run( host='192.168.110.6' )

