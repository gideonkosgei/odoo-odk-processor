import json
import logging
import odoorpc
from django.conf import settings
from rest_framework import status

logger = logging.getLogger(__name__)  # Get an instance of a logger


class OdkFormProcessor:
    def __init__(self, odk_form_data):
        self.odk_form_data = odk_form_data

    db_name = settings.ODOO_DB
    user_name = settings.ODOO_USER
    password = settings.ODOO_PASS
    host = settings.ODOO_HOST
    port = settings.ODOO_PORT

    # Prepare the connection to the server
    odoo = odoorpc.ODOO(host, protocol='jsonrpc', port=port)

    # login
    try:
        odoo.login(db_name, user_name, password)
    except Exception as e:
        logger.exception(e)

    # save submitted odk form
    def save_submission(self):

        try:
            model = 'health.odk.submission'
            json_data = json.loads(self.odk_form_data)

            payload = {
                'odk_submitted_object': json.dumps(json_data, indent=4, sort_keys=True),
                'is_processed': False
            }

            submission = self.odoo.env[model]
            submission.create(payload)
            response = 'processed successfully'

        except Exception as e:
            logger.exception(e)
            response = 'error'

        return response

    def get_submission(self):
        model = 'health.odk.submission'
        recs = self.odoo.execute(model, 'read', [13], ['odk_submitted_object'])
        return recs

    def save_submission_test(self):
        response_dict = ''

        try:
            model = 'health.config.catalogue'
            payload = {
                'catalogue_name': 'Test Category',
                'catalogue_description': 'Test Category'
            }
            submission = self.odoo.env[model]
            submission.create(payload)
            response_dict = {
                'code': status.HTTP_200_OK,
                'status': 'ok',
                'message': 'Record Successfully Created'
            }

        except odoorpc.error.RPCError as exc:
            logger.exception(exc.info)
            response_dict = {
                'code': status.HTTP_400_BAD_REQUEST,
                'status': 'error',
                'message': exc.info['data']['message']
            }

        return response_dict
