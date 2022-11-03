import json
from django.conf import settings
from .odoo import OdooProcessor


class OdkFormProcessor:
    def __init__(self, odk_form_data):
        self.odk_form_data = odk_form_data

        # save submitted odk form

    def save_submission(self):
        model = 'health.odk.submission'
        json_data = json.loads(self.odk_form_data)

        payload = {
            'odk_submitted_object': json.dumps(json_data, indent=4, sort_keys=True),
            'is_processed': False
        }

        odk = OdooProcessor(settings.ODOO_HOST, settings.ODOO_PORT, settings.ODOO_DB, settings.ODOO_USER,
                            settings.ODOO_PASS)

        system_id = odk.process(model, payload)
        print('Form Saved. Returned system ID :()'.format(system_id))

        return system_id


