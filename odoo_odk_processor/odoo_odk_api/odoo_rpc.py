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
        odoo.login(db_name, user_name, 'password')
    except Exception as e:
        logger.exception(e)

    # save submitted odk form
    def save_submission(self):
        try:
            req_body_len = len(self.odk_form_data.body)
            assert (req_body_len > 0)
        except AssertionError:
            logger.exception('The Submission Request Body Is Empty')
            response = {
                'code': status.HTTP_400_BAD_REQUEST,
                'status': 'error',
                'message': 'The Submission Request Body Is Empty'
            }
        else:
            try:
                model = 'health.odk.submission'
                # only process if request body has values
                json_data = json.loads(self.odk_form_data.body)
                json_data = json.dumps(json_data)

                payload = {
                    'odk_submitted_object': json_data,
                    'is_processed': False
                }

                submission = self.odoo.env[model]
                submission.create(payload)
                response = {
                    'code': status.HTTP_200_OK,
                    'status': 'ok',
                    'message': 'Record Recorded successfully'
                }
            except Exception as e:
                logger.exception(e)
                response = {
                    'code': status.HTTP_400_BAD_REQUEST,
                    'status': 'error',
                    'message': str(e)
                }

        return response

    def get_submissions(self):
        try:
            model = 'health.config.catalogue'
            # retrieve records where id is 1
            # recs = self.odoo.execute(model, 'read', [1], ['catalogue_name', 'catalogue_description'])
            # retrieve all records
            recs = self.odoo.execute(model, 'search_read', [], ['catalogue_name', 'catalogue_description'])

            response_dict = {
                'code': status.HTTP_200_OK,
                'status': 'ok',
                'message': 'Record Retrieved Successfully',
                'data': recs
            }
        except odoorpc.error.RPCError as exc:
            response_dict = {
                'code': status.HTTP_400_BAD_REQUEST,
                'status': 'error',
                'message': exc.info['data']['message']
            }
        except Exception as e:
            logger.exception(e)
            response_dict = {
                'code': status.HTTP_400_BAD_REQUEST,
                'status': 'error',
                'message': str(e)
            }

        return response_dict

    def get_submission_by_id(self, submission_id):
        try:
            model = 'health.odk.submission'
            # retrieve records where id is 1
            recs = self.odoo.execute(model, 'read', [submission_id], ['odk_submitted_object'])
            recs = json.loads(recs)

            response_dict = {
                'code': status.HTTP_200_OK,
                'status': 'ok',
                'message': 'Record Retrieved Successfully',
                'data': recs
            }
        except odoorpc.error.RPCError as exc:
            logger.exception(exc)
            response_dict = {
                'code': status.HTTP_400_BAD_REQUEST,
                'status': 'error',
                'message': exc.info['data']['message']
            }
        except Exception as e:
            logger.exception(e)
            response_dict = {
                'code': status.HTTP_400_BAD_REQUEST,
                'status': 'error',
                'message': str(e)
            }

        return response_dict

    def save_submission_test(self):
        
        try:
            model = 'health.config.catalogue'
            payload = {
                'catalogue_name': 'Test Category',
                'catalogue_description': 'Test Category'
            }
            submission = self.odoo.env[model]
            submission.create(payload)
            response = {
                'code': status.HTTP_200_OK,
                'status': 'ok',
                'message': 'Record Successfully Created'
            }

        except odoorpc.error.RPCError as exc:
            logger.exception(exc.info)
            response = {
                'code': status.HTTP_400_BAD_REQUEST,
                'status': 'error',
                'message': exc.info['data']['message']
            }

        return response
