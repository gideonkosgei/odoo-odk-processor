import json
import logging
import odoorpc
from django.conf import settings
from rest_framework import status
from datetime import datetime

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
    except odoorpc.error.RPCError as exc:
        logger.exception(exc.info['data']['message'])
    except Exception as e:
        logger.exception(e)

    # save submitted odk form
    def save_submission(self):
        record_id = None
        response = None
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
                # only process if request body has values
                json_data_obj = json.loads(self.odk_form_data.body)
                json_data_str = json.dumps(json_data_obj)

                # save the submitted json as a whole
                model_submission = 'health.odk.submission'
                payload_submission = {
                    'odk_submitted_object': json_data_str,
                    'is_processed': False
                }
                submission = self.odoo.env[model_submission]
                record_id = submission.create(payload_submission)
                logger.info("Submission with UUID {} Saved. Record ID Is {}".format(
                    json_data_obj['_uuid'], record_id))

                response = {
                    'code': status.HTTP_200_OK,
                    'status': 'ok',
                    'message': 'Record Recorded successfully'
                }

            except odoorpc.error.RPCError as exc:
                logger.exception(exc.info['data']['message'])
                response = {
                    'code': status.HTTP_400_BAD_REQUEST,
                    'status': 'error',
                    'message': exc.info['data']['message']
                }

            except Exception as e:
                logger.exception(e)
                response = {
                    'code': status.HTTP_400_BAD_REQUEST,
                    'status': 'error',
                    'message': str(e)
                }

        return response, record_id

    def save_farmer(self):
        record_id = None
        response = None
        try:
            # only process if request body has values
            json_data_obj = json.loads(self.odk_form_data.body)

            admin_unit = self.get_admin_units_using_least_admin_unit(json_data_obj["area/ward"])
            level_one_id = admin_unit['data'][0]['level_one_id'][0]
            level_two_id = admin_unit['data'][0]['level_two_id'][0]
            level_three_id = admin_unit['data'][0]['level_three_id'][0]
            level_four_id = admin_unit['data'][0]['id']

            # Register farmer
            model = 'health.farmer'

            visiting_date = json_data_obj[
                "area/visit_date"] if 'area/visit_date' in json_data_obj.keys() else datetime.now().strftime("%Y-%m-%d")
            farmer_phone_number = json_data_obj[
                "contact_information/farmer_phonenumber"] if "contact_information/farmer_phonenumber" in json_data_obj.keys() else ''
            visiting_doctor_name = json_data_obj[
                "contact_information/doctor_name"] if "contact_information/doctor_name" in json_data_obj.keys() else ''
            farmer_name = json_data_obj[
                "contact_information/farmer_name"] if "contact_information/farmer_name" in json_data_obj.keys() else ''
            country_id = json_data_obj["area/country"] if "area/country" in json_data_obj.keys() else ''

            payload = {
                'visiting_date': visiting_date,
                'visiting_doctor_name': visiting_doctor_name,
                'farmer_name': farmer_name,
                'farmer_phone_number': farmer_phone_number,
                'country_id': country_id,
                'level_one_id': level_one_id,
                'level_two_id': level_two_id,
                'level_three_id': level_three_id,
                'level_four_id': level_four_id
            }

            farmer = self.odoo.env[model]
            record_id = farmer.create(payload)
            logger.info("Farmer Registered. Record ID Is {}".format(record_id))

            response = {
                'code': status.HTTP_200_OK,
                'status': 'ok',
                'message': 'Record Recorded successfully'
            }

        except odoorpc.error.RPCError as exc:
            logger.exception(exc.info['data']['message'])
            response = {
                'code': status.HTTP_400_BAD_REQUEST,
                'status': 'error',
                'message': exc.info['data']['message']
            }

        except Exception as e:
            logger.exception(e)
            response = {
                'code': status.HTTP_400_BAD_REQUEST,
                'status': 'error',
                'message': str(e)
            }

        return response, record_id

    def save_animal_details(self, farm_id):
        record_id = None
        response = None
        try:
            # only process if request body has values
            json_data_obj = json.loads(self.odk_form_data.body)
            model_animal = 'health.animal'
            animals_array = json_data_obj["animalregistration"]

            for animal_array in animals_array:
                print('processing animal array')
                record_id = None
                response = None

                species_code = animal_array[
                    "animalregistration/animal_details/species"] if "animalregistration/animal_details/species" in animal_array.keys() else None

                animal_id = animal_array[
                    'animalregistration/animal_details/animal_id'] if 'animalregistration/animal_details/animal_id' in animal_array.keys() else None

                animal_age = animal_array[
                    'animalregistration/animal_details/animal_age'] if 'animalregistration/animal_details/animal_age' in animal_array.keys() else None

                animal_type_code = animal_array[
                    'animalregistration/animal_details/animal_type'] if 'animalregistration/animal_details/animal_type' in animal_array.keys() else None

                breed_code = animal_array[
                    'animalregistration/animal_details/animal_breed'] if 'animalregistration/animal_details/animal_breed' in animal_array.keys() else None

                # Animal Heat Details
                age_at_first_heat = animal_array[
                    'animalregistration/heat_details/heat_age'] if 'animalregistration/heat_details/heat_age' in animal_array.keys() else None

                show_sign_of_heat_after_first_heat_code = animal_array[
                    'animalregistration/heat_details/repeat_heat'] if 'animalregistration/heat_details/repeat_heat' in animal_array.keys() else None

                interval_btw_2_3_successive_heats = animal_array[
                    'animalregistration/heat_details/heat_interval'] if 'animalregistration/heat_details/heat_interval' in animal_array.keys() else None

                species = self.get_catalogue_item_id(21, species_code)
                animal_type = self.get_catalogue_item_id(14, animal_type_code)
                breed = self.search_for_breed_using_breed_code(breed_code)
                show_heat = self.get_catalogue_item_id(1, show_sign_of_heat_after_first_heat_code)

                species_id = species['data'][0]['id']
                animal_type_id = animal_type['data'][0]['id']
                breed_id = breed['data'][0]['id']
                show_heat_id = show_heat['data'][0]['id']

                payload_animal = {
                    'farmer_id': farm_id,
                    'animal_identification_number': animal_id,
                    'breed_id': breed_id,
                    'animal_age': animal_age,
                    'species_id': species_id,
                    'animal_type_id': animal_type_id,
                    'age_at_first_heat': age_at_first_heat,
                    'show_sign_of_heat_after_first_heat': show_heat_id,
                    'interval_btw_2_3_successive_heats': interval_btw_2_3_successive_heats
                }

                try:
                    animal = self.odoo.env[model_animal]
                    record_id = animal.create(payload_animal)
                    logger.info("Animal Registered. Record ID Is {}".format(record_id))
                    response = {
                        'code': status.HTTP_200_OK,
                        'status': 'ok',
                        'message': 'Record Recorded successfully'
                    }

                except odoorpc.error.RPCError as exc:
                    logger.exception(exc.info['data']['message'])
                    response = {
                        'code': status.HTTP_400_BAD_REQUEST,
                        'status': 'error',
                        'message': exc.info['data']['message']
                    }

        except Exception as e:
            logger.exception(e)
            response = {
                'code': status.HTTP_400_BAD_REQUEST,
                'status': 'error',
                'message': str(e)
            }

        return response, record_id

    def process(self):
        response = None
        submission_id = None
        farm_id = None
        animal_id = None
        try:
            response, submission_id = self.save_submission()  # save streamed submission

            if response.get('code') == 200:  # register farmer if submission is saved successfully
                response, farm_id = self.save_farmer()

            if response.get('code') == 200:  # register farmer if submission is saved successfully
                response, animal_id = self.save_animal_details(farm_id)

        except Exception as e:
            logger.exception(e)
            response = {
                'code': status.HTTP_400_BAD_REQUEST,
                'status': 'error',
                'message': str(e)
            }
        return response

    def save_submissionx(self):
        response = ""
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
                # only process if request body has values
                json_data_obj = json.loads(self.odk_form_data.body)
                json_data_str = json.dumps(json_data_obj)

                try:
                    # save the submitted json as a whole
                    model_submission = 'health.odk.submission'
                    payload_submission = {
                        'odk_submitted_object': json_data_str,
                        'is_processed': False
                    }
                    submission = self.odoo.env[model_submission]
                    submission_id = submission.create(payload_submission)
                    logger.info("Submission with UUID {} Saved. Record ID Is {}".format(
                        json_data_obj['_uuid'], submission_id))

                    # Register farmer
                    model_farmer = 'health.client'
                    payload_farmer = {
                        'client_name': json_data_obj["contact_information/farmer_name"],
                        'client_contact_number': json_data_obj["contact_information/doctor_name"],
                    }
                except odoorpc.error.RPCError as exc:
                    response = {
                        'code': status.HTTP_400_BAD_REQUEST,
                        'status': 'error',
                        'message': exc.info['data']['message']
                    }

                farmer = self.odoo.env[model_farmer]
                farmer_id = farmer.create(payload_farmer)
                logger.info("Farmer Registered. Record ID Is {}".format(farmer_id))

                # Register Animal + Related Details
                model_animal = 'health.animal'
                animals_array = json_data_obj["animalregistration"]

                for animal_array in animals_array:
                    print('processing animal array')

                    payload_animal = {
                        'client_id': farmer_id,
                        'animal_identification_number': animal_array['animalregistration/animal_details/animal_id'],
                        'breed_id': animal_array['animalregistration/animal_details/animal_breed'],
                        'animal_age': animal_array['animalregistration/animal_details/animal_age'],
                    }
                    print(payload_animal)
                    animal = self.odoo.env[model_animal]
                    animal_id = animal.create(payload_animal)
                    logger.info("Animal Registered. Record ID Is {}".format(animal_id))

                response = {
                    'code': status.HTTP_200_OK,
                    'status': 'ok',
                    'message': 'Record Recorded successfully'
                }
            except odoorpc.error.RPCError as exc:
                response = {
                    'code': status.HTTP_400_BAD_REQUEST,
                    'status': 'error',
                    'message': exc.info['data']['message']
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

    def get_admin_units_using_least_admin_unit(self, unit_id):
        try:
            model = 'health.admin.unit.level.four'
            recs = self.odoo.execute(model, 'search_read', [('level_code', '=', unit_id)],
                                     ['id', 'level_one_id', 'level_two_id', 'level_three_id'])

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

    def get_catalogue_item_id(self, catalogue_id, item_code):
        try:
            model = 'health.config.catalogue.item'
            recs = self.odoo.execute(model, 'search_read',
                                     [('catalogue_id', '=', catalogue_id), ('item_code', '=', item_code)],
                                     ['id', 'item_code', 'item_name', 'item_is_active', 'item_description'])

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

    def search_for_breed_using_breed_code(self, breed_code):
        try:
            model = 'health.breed'
            recs = self.odoo.execute(model, 'search_read',
                                     [('breed_code', '=', breed_code)],
                                     ['id', 'country_id', 'species_id', 'breed_code', 'breed_name', 'breed_is_active'])
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
