#!/usr/bin/python

from flask import Flask, render_template, request
app = Flask( __name__ )

from dnsmasq import dnshosts, dnsconfig

CONFIG_PATH='/root/dnsmasq/dnsmasq.conf'
MAC_FORM_MAX=2

def save_config( key, pattern, update, linewriter, path=CONFIG_PATH ):
    # Merge updates with existing records and convert them to config lines.
    old_list = dnsconfig.parse_lines( pattern, path )
    old_list = dnsconfig.merge_update( old_list, key, update )
    lines = []
    for item in old_list:
        line = linewriter( item )
        if 'disabled' in item and item['disabled']:
            line = '#' + line
        lines += [line]

    # Load the existing config and apply the changes.
    new_conf = dnsconfig.read_config( CONFIG_PATH, [pattern] )
    new_conf += lines

    return '\n'.join( new_conf )

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
    if not request.form.get( 'enabled' ):
        new_cname['disabled'] = True

    return save_config(
        'source', dnsconfig.RE_CNAME, new_cname,
        lambda x: 'cname={},{}'.format( x['source'], x['dest'] ) )

@app.route( '/interfaces' )
def route_interfaces():
    interfaces = dnsconfig.parse_lines( dnsconfig.RE_INTERFACE, CONFIG_PATH )
    return render_template( 'interfaces.html', interfaces=interfaces )

@app.route( '/hosts' )
def route_hosts():
    dns_hosts = dnshosts.read_hosts( '/root/dnsmasq/dnsmasq/hosts/hosts' )
    dns_res = dnsconfig.parse_lines(
        dnsconfig.RE_RESERVATION, path=CONFIG_PATH, key='ip' )
    dns_res_multimac = []
    
    # Add missing hosts to res list so MAC field gets filled out below.
    for host in dns_hosts:
        if host['ip'] not in dns_res:
            dns_res[host['ip']] = {'mac': '', 'ip': host['ip']}

    # Make sure we always have the same number of MAC fields.
    for res_key, res in dns_res.items():
        res['mac'] = res['mac'].split( ',' )
        while MAC_FORM_MAX > len( res['mac'] ):
            res['mac'] += ['']
        dns_res_multimac += [res]
    
    combined = dnshosts.combine_host_reservations( dns_hosts, dns_res_multimac )
    return render_template( 'hosts.html', hosts=combined )

@app.route( '/hosts/save', methods=['POST'] )
def route_hosts_save():
    for key, item in request.form.iteritems():
        print key

    # Build the edit object.
    new_res = {}
    new_res['ip'] = request.form.get( 'ip' )
    new_res['name'] = request.form.get( 'name' )
    new_res['mac'] = request.form.getlist( 'mac' )
    if not request.form.get( 'enabled' ):
        new_res['disabled'] = True

    return save_config(
        'ip', dnsconfig.RE_RESERVATION, new_res,
        lambda x: 'dhcp-host={},{}'.format(
            ','.join( x['mac'] ) if type( x['mac'] ) == list else x['mac'],
            x['ip'] ) )

@app.route( '/' )
def route_root():
    options = dnsconfig.parse_lines( dnsconfig.RE_OPTIONS, CONFIG_PATH )
    return render_template(
        'index.html', options=options, empty_options=dnsconfig.EMPTY_OPTIONS )

if '__main__' == __name__:
	app.run( host='192.168.110.6' )

