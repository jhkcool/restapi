#coding=utf-8

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.conf.urls import url as make_url
from django.conf import settings
from django.db import connections

from exceptions import APIError

import cProfile
import pstats
import resource
import time
import urls
import json
import inspect


def inspect_func(func):
    if hasattr(func, 'rest_spec'):
        return func.rest_spec

    result = {
        'module': inspect.getmodule(func).__name__,
        'name': func.func_name,
        'doc': func.__doc__,
        'params': [],
    }

    arg_spec = inspect.getargspec(func)
    result['args'] = arg_spec.varargs
    result['kwargs'] = arg_spec.keywords

    arg_count = 0
    default_count = len(arg_spec.defaults) if arg_spec.defaults else 0
    default_start = len(arg_spec.args) - default_count

    for arg in arg_spec.args:
        if arg_count >= default_start:
            default_value = arg_spec.defaults[arg_count-default_start]
            required = False
        else:
            default_value = None
            required = True

        result['params'].append({
            'name': arg,
            'required': required,
            'default':  default_value,
        })
        arg_count += 1

    func.rest_spec = result
    return result


api_table = {}


def api(api_func=None, name=None, group=None, url=None, types=None):
    
    def wrapper(func):
        rest_spec = inspect_func(func)

        if types:
            for param in rest_spec['params']:
                if param['name'] in types:
                    param['type'] = types[param['name']]
                    param['type_name'] = types[param['name']].__name__
                else:
                    param['type'] = None
                    param['type_name'] = u'任意'

        if group not in api_table:
            api_table[group] = {}

        api_name = name if name else rest_spec['name']

        if api_name in api_table[group]:
            raise Exception('duplicate api name %s with function %s' % (api_name, rest_spec['name']))

        api_prefix = '^%s/'%group if group else '^'
        api_postfix = '/$'

        if not url:
            api_url = api_prefix + api_name + api_postfix
        else:
            api_url = api_prefix + url + api_postfix

        api_table[group][api_name] = {
            'spec': rest_spec,
            'url': api_url
        }

        @csrf_exempt
        def django_view(request, *args, **kwargs):
            if request.method == 'POST' and request.META['CONTENT_TYPE'].startswith('application/json'):
                body = json.loads(request.body)
            else:
                body = {}

            params = {}
            varg = 0

            try:
                for param in rest_spec['params']:
                    name, required, default = param['name'], param['required'], param['default']

                    if len(args) > varg:
                        params[name] = args[varg]
                        varg += 1
                    elif name in kwargs:
                        params[name] = kwargs[name]

                    elif name in request.GET:
                        params[name] = request.GET[name]
                    elif name in request.POST:
                        params[name] = request.POST[name]
                    elif name in body:
                        params[name] = body[name]

                    elif not required:
                        params[name] = default

                    if param.has_key('type'):
                        value = params[name]
                        if isinstance(value, dict):
                            params[name] = param['type'](**value)
                        else:
                            params[name] = param['type'](value)
            except Exception as ex:
                e = {
                    'message': str(ex)
                }
                response = HttpResponse(json.dumps(e))
                response.status_code = 400
                return response

            try:
                profile = cProfile.Profile()
                start_time = time.time()
                start_rusage = resource.getrusage(resource.RUSAGE_SELF)
                response = HttpResponse(content_type='application/json')

                result = profile.runcall(func, **params)

                response.content = json.dumps(result, indent=2)
            except APIError as err:
                response.status_code = err.status
                response.content = json.dumps(err.data)
            except Exception as ex:
                traces = []
                start_trace = False

                for fr, fi, li, fn, cb, _ in inspect.trace():
                    if fn == 'runcall':
                        start_trace = True
                        continue
                    if start_trace:
                        traces.append({
                            'file': fi,
                            'line': li,
                            'func': fn,
                            'code': cb
                        })

                e = {
                    'message': str(ex),
                    'stacktrace': traces
                }
                response.status_code = 500
                response.content = json.dumps(e)
            finally:
                end_time = time.time()
                end_rusage = resource.getrusage(resource.RUSAGE_SELF)

                timer = {
                    'start': start_time,
                    'end': end_time,
                    'elapsed': (end_time - start_time)*1000,
                    'utime': (end_rusage.ru_utime - start_rusage.ru_utime)*1000,
                    'stime': (end_rusage.ru_stime - start_rusage.ru_stime)*1000,
                    'nvcsw': end_rusage.ru_nvcsw - start_rusage.ru_nvcsw,
                    'nivcsw': end_rusage.ru_nivcsw - start_rusage.ru_nivcsw,
                }
                response['timer'] = json.dumps(timer)

                sql = {}
                for db in settings.DATABASES:
                    sql[db] = connections[db].queries
                response['sql'] = json.dumps(sql)

                profiling = []
                profile.create_stats()
                stats = pstats.Stats(profile)
                stats.calc_callees()

                for (filepath, line, func_name), (cc, nc, tt, ct, _) in stats.stats.items()[:10]:
                    profiling.append((filepath, line, func_name, cc, nc, tt*1000, ct*1000))
                    profiling.sort(lambda a, b: 1 if a[6]<b[6] else -1)

                response['profiling'] = json.dumps(profiling[:10])
                return response
            
        urlpattern = make_url(api_url, django_view)
        urls.urlpatterns.append(urlpattern)
        return func

    if api_func:
        return wrapper(api_func)
    else:
        return wrapper

