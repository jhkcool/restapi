#coding=utf-8

from django.core.management import BaseCommand

from restapi.decorators import api_table


class Command(BaseCommand):

    def handle(self, *args, **options):
        print api_table