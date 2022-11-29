from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from .odoo_rpc import OdkFormProcessor
import json
import logging  # import the logging library

logger = logging.getLogger(__name__)  # Get an instance of a logger


class WelcomeApiView(APIView):

    @staticmethod
    def get(request, *args, **kwargs):
        print('welcome message')
        return Response('Odoo-ODK(Open Data Kit) processor', status=status.HTTP_200_OK)


class OdooApiView(APIView):

    @staticmethod
    @csrf_exempt
    def post(request, *args, **kwargs):
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>> ODK Webhook Callback >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        rpc = OdkFormProcessor(request)
        response = rpc.process()
        return Response(response, status=response['code'])

    @staticmethod
    def get(request, *args, **kwargs):
        rpc = OdkFormProcessor('')
        # response = rpc.get_submission_by_id(15)
        # response = rpc. get_admin_units_using_least_admin_unit(25025)
        response = rpc.get_catalogue_item_id(1, 2)
        response = rpc.search_for_breed_using_breed_code(6)

        return Response(response, status=response["code"])
