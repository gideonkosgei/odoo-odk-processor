from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from .odoo_rpc import OdkFormProcessor
import json
import logging  # import the logging library
import odoorpc

logger = logging.getLogger(__name__)  # Get an instance of a logger


class WelcomeApiView(APIView):

    @staticmethod
    def get(request, *args, **kwargs):
        return Response('Odoo-ODK(Open Data Kit) processor', status=status.HTTP_200_OK)


class OdooApiView(APIView):

    @staticmethod
    @csrf_exempt
    def post(request, *args, **kwargs):
        logger.info(request)

        try:
            req_body_len = len(request.body)
            assert (req_body_len > 0)
        except AssertionError:
            logger.exception('The Submission Request Body Is Empty. Data Cannot Be Processed. Exiting...')
        else:
            try:
                # only process if request body has values
                json_data = json.loads(request.body)
                json_data_formatted = json.dumps(json_data, indent=4, sort_keys=True)
                rpc = OdkFormProcessor(json_data_formatted)
                rpc.save_submission()
                logger.info('Post Request From Ona Received & Processed successfully')
            except Exception as e:
                logger.exception(e)

        return Response({'response': True}, status=status.HTTP_200_OK)
