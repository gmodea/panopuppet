from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.cache import cache_page
from pano.methods.dictfuncs import dictstatus as dictstatus
from pano.puppetdb.pdbutils import run_puppetdb_jobs
from pano.settings import CACHE_TIME
from pano.puppetdb.puppetdb import set_server, get_server
from pano.views.views import default_context
__author__ = 'etaklar'


@login_required
@cache_page(CACHE_TIME)
def dashboard(request, certname=None):
    context = default_context
    if request.method == 'GET':
        if 'source' in request.GET:
            source = request.GET.get('source')
            set_server(request, source)
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return redirect(request.POST['url'])

    source_url, source_certs, source_verify = get_server(request)
    puppet_run_time = get_server(request, type='run_time')
    events_params = {
        'query':
            {
                1: '["and",["=","latest-report?",true],["in", "certname",["extract", "certname",["select-nodes",["null?","deactivated",true]]]]]'
            },
        'summarize-by': 'certname',
    }
    nodes_params = {
        'limit': 25,
        'order-by': {
            'order-field': {
                'field': 'report-timestamp',
                'order': 'desc',
            },
            'query-field': {'field': 'certname'},
        },
    }

    jobs = {
        'population': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'id': 'population',
            'path': '/metrics/mbean/com.puppetlabs.puppetdb.query.population:type=default,name=num-nodes',
        },
        'tot_resource': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'id': 'tot_resource',
            'path': '/metrics/mbean/com.puppetlabs.puppetdb.query.population:type=default,name=num-resources',
        },
        'avg_resource': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'id': 'avg_resource',
            'path': '/metrics/mbean/com.puppetlabs.puppetdb.query.population:type=default,name=avg-resources-per-node',
        },
        'all_nodes': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'api_version': 'v4',
            'id': 'all_nodes',
            'path': '/nodes',
        },
        'events': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'id': 'event-counts',
            'path': 'event-counts',
            'api_version': 'v4',
            'params': events_params,
        },
        'nodes': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'api_version': 'v4',
            'id': 'nodes',
            'path': '/nodes',
            'params': nodes_params,
        },
    }
    puppetdb_results = run_puppetdb_jobs(jobs)
    # Dashboard to show nodes of "recent, failed, unreported or changed"
    dashboard_show = request.GET.get('show', 'recent')

    # Assign vars from the completed jobs
    puppet_population = puppetdb_results['population']
    # Total resources managed by puppet metric
    total_resources = puppetdb_results['tot_resource']
    # Average resource per node metric
    avg_resource_node = puppetdb_results['avg_resource']
    # Information about all active nodes in puppet
    all_nodes_list = puppetdb_results['all_nodes']
    # All available events for the latest puppet reports
    event_list = puppetdb_results['event-counts']
    node_list = puppetdb_results['nodes']

    failed_list, changed_list, unreported_list, mismatch_list, pending_list = dictstatus(all_nodes_list,
                                                                                         event_list,
                                                                                         sort=True,
                                                                                         sortby='latestReport',
                                                                                         get_status='notall',
                                                                                         puppet_run_time=puppet_run_time)
    pending_list = [x for x in pending_list if x not in unreported_list]
    changed_list = [x for x in changed_list if
                    x not in unreported_list and x not in failed_list and x not in pending_list]
    failed_list = [x for x in failed_list if x not in unreported_list]
    unreported_list = [x for x in unreported_list if x not in failed_list]

    if dashboard_show == 'recent':
        merged_nodes_list = dictstatus(
            node_list, event_list, sort=False, get_status="all", puppet_run_time=puppet_run_time)
    elif dashboard_show == 'failed':
        merged_nodes_list = failed_list
    elif dashboard_show == 'unreported':
        merged_nodes_list = unreported_list
    elif dashboard_show == 'changed':
        merged_nodes_list = changed_list
    elif dashboard_show == 'failed_catalogs':
        merged_nodes_list = mismatch_list
    elif dashboard_show == 'pending':
        merged_nodes_list = pending_list
    else:
        merged_nodes_list = dictstatus(
            node_list, event_list, sort=False, get_status="all", puppet_run_time=puppet_run_time)

    node_unreported_count = len(unreported_list)
    node_fail_count = len(failed_list)
    node_change_count = len(changed_list)
    node_off_timestamps_count = len(mismatch_list)
    node_pending_count = len(pending_list)
    context['node_list'] = merged_nodes_list
    context['certname'] = certname
    context['show_nodes'] = dashboard_show
    context['population'] = puppet_population['Value']
    context['total_resource'] = total_resources['Value']
    context['avg_resource'] = "{:.2f}".format(avg_resource_node['Value'])
    context['failed_nodes'] = node_fail_count
    context['changed_nodes'] = node_change_count
    context['unreported_nodes'] = node_unreported_count
    context['weird_timestamps'] = node_off_timestamps_count
    context['pending_nodes'] = node_pending_count

    return render(request, 'pano/index.html', context)
