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
    response = ''

    @staticmethod
    @csrf_exempt
    def post(request, *args, **kwargs):
        logger.info(request)

        try:
            rpc = OdkFormProcessor('')
            response = rpc.save_submission_test()

        except Exception as e:
            logger.exception(e)
            response = {
                'code': status.HTTP_400_BAD_REQUEST,
                'status': 'error',
                'message': e
            }

        try:
            req_body_len = len(request.body)
            assert (req_body_len > 0)
        except AssertionError:
            logger.exception('The Submission Request Body Is Empty. Data Cannot Be Processed. Exiting...')
            response = {
                'code': status.HTTP_400_BAD_REQUEST,
                'status': 'error',
                'message': 'The Submission Request Body Is Empty'
            }
        else:
            try:
                # only process if request body has values
                json_data = json.loads(request.body)
                json_data_formatted = json.dumps(json_data, indent=4, sort_keys=True)
                rpc = OdkFormProcessor(json_data_formatted)
                response = rpc.save_submission()
                logger.info('Post Request From Ona Received & Processed successfully')

            except Exception as e:
                logger.exception(e)
                response = {
                    'code': status.HTTP_400_BAD_REQUEST,
                    'status': 'error',
                    'message': e
                }

        return Response(response, status=response["code"])
