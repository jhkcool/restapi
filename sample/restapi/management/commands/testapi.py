#coding=utf-8

from django.core.management import BaseCommand

from restapi.decorators import api_table


class Command(BaseCommand):

    help = u'调试API'

    def handle(self, *args, **options):
        print api_table