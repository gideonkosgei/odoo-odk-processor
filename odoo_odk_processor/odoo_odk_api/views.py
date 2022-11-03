from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from .odk_forms import OdkFormProcessor
import json
import logging  # import the logging library

logger = logging.getLogger(__name__)  # Get an instance of a logger


class WelcomeApiView(APIView):

    @staticmethod
    def get(request, *args, **kwargs):
        return Response('Odoo-ODK(Open Data Kit) processor', status=status.HTTP_200_OK)


class OdooApiView(APIView):

    @staticmethod
    @csrf_exempt
    def post(request, *args, **kwargs):
        logger.warning('post request received')
        logger.info("This logs an info message.")
        logger.error("This logs an error message.")

        if len(request.body) > 0:
            json_data = json.loads(request.body)
            json_data_formatted = json.dumps(json_data, indent=4, sort_keys=True)
            odk_form = OdkFormProcessor(json_data_formatted)

            # Save ODK form submission
            odk_form.save_submission()

        print('The api has been invoked')

        return Response({'response': True}, status=status.HTTP_200_OK)
