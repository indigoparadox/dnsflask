#!/usr/bin/python
# vim: ai ts=4 sw=4 ss=4

import argparse
import logging
from flask import Flask, render_template, request, Blueprint, current_app, abort, redirect

from dnsmasq import dnshosts, dnsconfig

MAC_FORM_MAX=2

bp = Blueprint( 'dnsflask', __name__, template_folder='templates' )

def rest_object( keys ):

    if 'Delete' == request.form.get( 'action' ):
        # TODO
        return None

    # Discard empty ifnames.
    if '' == request.form.get( 'name' ):
        return None

    # Build the edit object.
    rest_obj = {}
    for key in keys:
        rest_obj[key] = request.form.get( key )
    if request.form.get( 'enabled' ):
        rest_obj['disabled'] = ''
    else:
        rest_obj['disabled'] = '#'

    return rest_obj

def save_config( key, pattern, update, linewriter, path ):
    logger = logging.getLogger( 'config.save' )
    # Merge updates with existing records and convert them to config lines.
    old_list = []
    try:
        old_list = dnsconfig.parse_lines( pattern, path )
    except IOError as e:
        logger.error( e )
    old_list = dnsconfig.merge_update( old_list, key, update )
    lines = []
    for item in old_list:
        line = linewriter( item )
        if 'disabled' in item and '#' == item['disabled']:
            line = '#' + line
        lines += [line]

    # Load the existing config and apply the changes.
    new_conf = []
    try:
        new_conf = dnsconfig.read_config( path, [pattern] )
    except IOError as e:
        logger.error( e )
    new_conf += lines

    #return '\n'.join( new_conf )
    with open( path, 'w' ) as new_conf_file:
        new_conf_file.write( '\n'.join( new_conf ) )

@bp.route( '/servers' )
def route_servers():
    logger = logging.getLogger( 'route.servers' )
    servers = ''
    try:
        servers = dnsconfig.parse_lines(
            dnsconfig.RE_SERVER, current_app.config_path )
    except IOError as e:
        logger.error( e )
    return render_template( 'servers.html', servers=servers )

@bp.route( '/cnames' )
def route_cnames():
    logger = logging.getLogger( 'route.cnames' )
    cnames = ''
    try:
        cnames = dnsconfig.parse_lines(
            dnsconfig.RE_CNAME, current_app.config_path )
    except IOError as e:
        logger.error( e )
    return render_template( 'cnames.html', cnames=cnames )

@bp.route( '/cnames/save', methods=['POST'] )
def route_cnames_save():
    logger = logging.getLogger( 'route.cnames.save' )

    new_cname = rest_object( ['source', 'dest'] )
    logger.info( 'Saving config item: {}'.format( new_cname ) )
    save_config(
        'source', dnsconfig.RE_CNAME, new_cname,
        lambda x: 'cname={},{}'.format( x['source'], x['dest'] ),
        current_app.config_path )

    return redirect( '/cnames', code=302 )

@bp.route( '/interfaces' )
def route_interfaces():
    logger = logging.getLogger( 'route.interfaces' )
    interfaces = ''
    try:
        interfaces = dnsconfig.parse_lines(
            dnsconfig.RE_INTERFACE, current_app.config_path )
    except IOError as e:
        logger.error( e )
    return render_template( 'interfaces.html', interfaces=interfaces )

@bp.route( '/interfaces/save', methods=['POST'] )
def route_interfaces_save():
    logger = logging.getLogger( 'route.interfaces.save' )

    new_if = rest_object( ['interface'] )
    logger.info( 'Saving config item: {}'.format( new_if ) )
    save_config(
        'interface', dnsconfig.RE_INTERFACE, new_if,
        lambda x: 'interface={}'.format( x['interface'] ),
        current_app.config_path )

    return redirect( '/interfaces', code=302 )

@bp.route( '/hosts' )
def route_hosts():
    logger = logging.getLogger( 'route.hosts' )

    dns_hosts = []
    try:
        dns_hosts = dnshosts.read_hosts( current_app.hosts_path )
    except IOError as e:
        logger.error( e )
    dns_res = dnsconfig.parse_lines(
        dnsconfig.RE_RESERVATION, path=current_app.config_path, key='ip' )
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

@bp.route( '/hosts/save', methods=['POST'] )
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

    save_config(
        'ip', dnsconfig.RE_RESERVATION, new_res,
        lambda x: 'dhcp-host={},{}'.format(
            ','.join( x['mac'] ) if type( x['mac'] ) == list else x['mac'],
            x['ip'] ),
        current_app.config_path )

@bp.route( '/' )
def route_root():
    logger = logging.getLogger( 'route.root' )
    logger.info( 'Request: /, Config: {}'.format( current_app.config_path ) )
    options = {}
    try:
        options = dnsconfig.parse_lines( 
            dnsconfig.RE_OPTIONS, current_app.config_path )
    except IOError as e:
        logger.error( e )

    return render_template(
        'index.html', options=options,
        empty_options=dnsconfig.EMPTY_OPTIONS )

def create_flask( config_path, hosts_path ):
    global bp
    
    app = Flask( __name__ )
    app.config_path = config_path
    app.hosts_path = hosts_path
    app.register_blueprint( bp )
    return app

if '__main__' == __name__:

    logging.basicConfig( level=logging.INFO )

    cli = argparse.ArgumentParser()

    cli.add_argument( '-c', '--config', action='store',
        default='/etc/dnsmasq.conf',
        help='Path to config file from which to get initial settings.' )

    cli.add_argument( '-o', '--hosts', action='store',
        default='/etc/hosts',
        help='Path to hosts file from which to get hosts.' )

    cli.add_argument( 'hostname', action='store', default='127.0.0.1',
        help='Hostname or IP on which to listen.' )

    #cli.add_argument( 'port', action='store', default=5000,
    #    help='Hostname or IP on which to listen.' )

    args = cli.parse_args()

    app = create_flask( args.config, args.hosts )
    app.run( host=args.hostname )

