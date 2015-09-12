#coding=utf-8

from django.shortcuts import render
from restapi.decorators import api_table


def document(request):
    return render(request, 'restapi/document.html', {
        'apis': api_table
    })


def debug(request):
    return render(request, 'restapi/debug.html', {
        'apis': api_table
    })


def client_jquery(request):
    return render(request, 'restapi/client_jquery.js', {
        'apis': api_table
    }, content_type='application/x-javascript;charset=utf-8')    


def client_ng(request):
    return render(request, 'restapi/client_ng.js', {
        'apis': api_table
    }, content_type='application/x-javascript;charset=utf-8')    

