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

    # Extract Values From ODK Submitted Object
    def get_odk_values(self, array, attribute, is_lookup, catalogue):
        value = array[attribute] if attribute in array.keys() else None
        if is_lookup and value is not None:
            value_array = self.get_catalogue_item_id(catalogue, value)
            return value_array['data'][0]['id']
        elif not is_lookup and value is not None:
            return value
        else:
            return None

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

            farm_object = json.loads(self.odk_form_data.body)
            admin_unit = self.get_admin_units_using_least_admin_unit(farm_object["area/ward"])
            level_one_id = admin_unit['data'][0]['level_one_id'][0]
            level_two_id = admin_unit['data'][0]['level_two_id'][0]
            level_three_id = admin_unit['data'][0]['level_three_id'][0]
            level_four_id = admin_unit['data'][0]['id']

            model = 'health.farmer'


            visiting_date = self.get_odk_values(farm_object, 'area/visit_date', False, None)
            visiting_date = datetime.now().strftime("%Y-%m-%d") if visiting_date is None else visiting_date
            country_id = self.get_odk_values(farm_object, 'area/country', False, None)

            # Lab Tests
            group_key = 'grp_feeds/'
            nutritional_plan = self.get_odk_values(farm_object, group_key + 'feed_type', True, 17)
            regular_supply_of_minerals_and_vitamins = self.get_odk_values(farm_object, group_key + 'mineral_supply',
                                                                          True, 2)
            # Farmer Details
            group_key = 'farm_registration/'
            farmer_phone_number = self.get_odk_values(farm_object, group_key + 'farmer_phonenumber',
                                                      False, None)
            farmer_name = self.get_odk_values(farm_object,  group_key + 'farmer_name', False, None)
            farm_type = self.get_odk_values(farm_object, group_key + 'farm_type', True, 24)
            age_group = self.get_odk_values(farm_object, group_key + 'farmer_age', True, 25)
            gender = self.get_odk_values(farm_object, group_key + 'farmer_gender', True, 26)

            payload = {
                'visiting_date': visiting_date,
                'farmer_name': farmer_name,
                'farmer_phone_number': farmer_phone_number,
                'country_id': country_id,
                'level_one_id': level_one_id,
                'level_two_id': level_two_id,
                'level_three_id': level_three_id,
                'level_four_id': level_four_id,
                'nutritional_plan': nutritional_plan,
                'regular_supply_of_minerals_and_vitamins': regular_supply_of_minerals_and_vitamins,
                'farm_type': farm_type,
                'age_group': age_group,
                'gender': gender
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

    def save_vaccination_record(self, odk_object, animal_id):
        record_id = None
        response = None
        try:
            print('Entered Vaccination Module.....')
            model = 'health.vaccination'
            group_key = 'animalregistration/repeat_vaccinetype/treatment_diseases/'

            for vax in odk_object:
                print('Processing Vaccination Record')
                record_id = None
                response = None

                vaccine_id = self.get_odk_values(vax, group_key + 'vaccine_type', True, 22)
                vaccination_date = self.get_odk_values(vax, group_key + 'vaccination_date',
                                                       False, None)
                payload = {
                    'animal_id': animal_id,
                    'vaccine_id': vaccine_id,
                    'vaccination_date': vaccination_date
                }

                try:
                    vaccine = self.odoo.env[model]
                    record_id = vaccine.create(payload)
                    logger.info("vaccination Record Created. Record ID Is {}".format(record_id))

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

    def save_deworming_record(self, odk_object, animal_id):
        record_id = None
        response = None
        try:
            print('Entered De-worming Module.....')
            model = 'health.deworming'
            group_key = 'animalregistration/repeat_dewormingdate/grp_deworming/'

            for deworm in odk_object:
                print('Processing De-worming Record')
                record_id = None
                response = None
                deworming_date = self.get_odk_values(deworm, group_key + 'deworming_date',
                                                     False, None)
                payload = {
                    'animal_id': animal_id,
                    'deworming_date': deworming_date
                }

                try:
                    worm = self.odoo.env[model]
                    record_id = worm.create(payload)
                    logger.info("De-worming Record Created. Record ID Is {}".format(record_id))

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
        animal_id = None
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

                # Calving Details
                age_at_first_calving = animal_array[
                    'animalregistration/animal_calving/calving_age'] if 'animalregistration/animal_calving/calving_age' in animal_array.keys() else None

                number_of_lactation = animal_array[
                    'animalregistration/animal_calving/parity'] if 'animalregistration/animal_calving/parity' in animal_array.keys() else None

                time_interval_btw_last_calving_to_next_heat = animal_array[
                    'animalregistration/animal_calving/calving_heatinterval'] if 'animalregistration/animal_calving/calving_heatinterval' in animal_array.keys() else None

                time_interval_btw_last_calving_to_next_conception = animal_array[
                    'animalregistration/animal_calving/calving_conceptioninterval'] if 'animalregistration/animal_calving/calving_conceptioninterval' in animal_array.keys() else None

                # Breed
                date_of_service = animal_array[
                    'animalregistration/Breeding_details/service_date'] if 'animalregistration/Breeding_details/service_date' in animal_array.keys() else None

                type_of_mating_code = animal_array[
                    'animalregistration/Breeding_details/breeding_method'] if 'animalregistration/Breeding_details/breeding_method' in animal_array.keys() else None

                gestation_months = animal_array[
                    'animalregistration/Breeding_details/gestation_months'] if 'animalregistration/Breeding_details/gestation_months' in animal_array.keys() else None

                ai_conceptions = animal_array[
                    'animalregistration/Breeding_details/ai_conceptions'] if 'animalregistration/Breeding_details/ai_conceptions' in animal_array.keys() else None

                animal_conceived_code = animal_array[
                    'animalregistration/Breeding_details/animal_conceived'] if 'animalregistration/Breeding_details/animal_conceived' in animal_array.keys() else None

                # Fertility Details
                dystocia_code = animal_array[
                    'animalregistration/fertility_details/suffer_dystocia'] if 'animalregistration/fertility_details/suffer_dystocia' in animal_array.keys() else None

                dystocia_foetus_status_code = animal_array[
                    'animalregistration/fertility_details/foetus_status'] if 'animalregistration/fertility_details/foetus_status' in animal_array.keys() else None

                delayed_post_partum_heat_code = animal_array[
                    'animalregistration/fertility_details/suffer_delayedheat'] if 'animalregistration/fertility_details/suffer_delayedheat' in animal_array.keys() else None

                delayed_post_partum_heat_length = animal_array[
                    'animalregistration/fertility_details/delayedheat_period'] if 'animalregistration/fertility_details/delayedheat_period' in animal_array.keys() else None

                retention_of_placenta_code = animal_array[
                    "animalregistration/fertility_details/suffer_retainedplacenta"] if "animalregistration/fertility_details/suffer_retainedplacenta" in animal_array.keys() else None

                retention_of_placenta_count = animal_array[
                    'animalregistration/fertility_details/retainedplacenta_times'] if 'animalregistration/fertility_details/retainedplacenta_times' in animal_array.keys() else None

                abortion_code = animal_array[
                    'animalregistration/fertility_details/suffer_abortion'] if 'animalregistration/fertility_details/suffer_abortion' in animal_array.keys() else None

                abortion_count = animal_array[
                    'animalregistration/fertility_details/abortion_times'] if 'animalregistration/fertility_details/abortion_times' in animal_array.keys() else None

                abortion_month = animal_array[
                    'animalregistration/fertility_details/abortion_month'] if 'animalregistration/fertility_details/abortion_month' in animal_array.keys() else None

                still_birth_code = animal_array[
                    'animalregistration/fertility_details/suffer_stillbirth'] if 'animalregistration/fertility_details/suffer_stillbirth' in animal_array.keys() else None

                still_birth_count = animal_array[
                    'animalregistration/fertility_details/stillbirth_times'] if 'animalregistration/fertility_details/stillbirth_times' in animal_array.keys() else None

                # Disease & Condition

                mastitis_code = animal_array[
                    'animalregistration/history_diseases/suffer_mastitis'] if 'animalregistration/history_diseases/suffer_mastitis' in animal_array.keys() else None
                mastitis_quarters_affected = animal_array[
                    'animalregistration/history_diseases/quarters_affected'] if 'animalregistration/history_diseases/quarters_affected' in animal_array.keys() else None
                teat_canal_blockage_code = animal_array[
                    'animalregistration/history_diseases/canal_blockage'] if 'animalregistration/history_diseases/canal_blockage' in animal_array.keys() else None

                udder_fibrotic_change_code = animal_array[
                    'animalregistration/history_diseases/fibrotic_udder'] if 'animalregistration/history_diseases/fibrotic_udder' in animal_array.keys() else None
                udder_fibrotic_change_status_code = animal_array[
                    'animalregistration/history_diseases/fibrotic_change'] if 'animalregistration/history_diseases/fibrotic_change' in animal_array.keys() else None

                lameness_history_code = animal_array[
                    'animalregistration/history_diseases/lameness_treat'] if 'animalregistration/history_diseases/lameness_treat' in animal_array.keys() else None
                lameness_treatment = animal_array[
                    'animalregistration/history_diseases/lameness_treatmenttype'] if 'animalregistration/history_diseases/lameness_treatmenttype' in animal_array.keys() else None

                hip_dislocation_fracture_history_code = animal_array[
                    'animalregistration/history_diseases/suffer_hipdislocation'] if 'animalregistration/history_diseases/suffer_hipdislocation' in animal_array.keys() else None
                duration_of_the_existing_disease = animal_array[
                    'animalregistration/history_diseases/dislocation_period'] if 'animalregistration/history_diseases/dislocation_period' in animal_array.keys() else None

                repeat_breeding_code = animal_array[
                    'animalregistration/history_diseases/suffer_repeatbreeding'] if 'animalregistration/history_diseases/suffer_repeatbreeding' in animal_array.keys() else None
                repeat_breeding_count = animal_array[
                    'animalregistration/history_diseases/breeding_times'] if 'animalregistration/history_diseases/breeding_times' in animal_array.keys() else None

                # General Appearance
                general_appearance_code = animal_array[
                    'animalregistration/grp_appearance/Assessment_appearance'] if 'animalregistration/grp_appearance/Assessment_appearance' in animal_array.keys() else None

                body_coat_code = animal_array[
                    'animalregistration/grp_appearance/assesment_bodycoat'] if 'animalregistration/grp_appearance/assesment_bodycoat' in animal_array.keys() else None

                general_health_condition_code = animal_array[
                    'animalregistration/grp_appearance/assessment_bodycondition'] if 'animalregistration/grp_appearance/assessment_bodycondition' in animal_array.keys() else None

                appetite_code = animal_array[
                    'animalregistration/grp_appearance/assessment_appetite'] if 'animalregistration/grp_appearance/assessment_appetite' in animal_array.keys() else None

                eyes_code = animal_array[
                    'animalregistration/grp_appearance/assessment_eyes'] if 'animalregistration/grp_appearance/assessment_eyes' in animal_array.keys() else None

                group_key = 'animalregistration/animal_details/'
                dob_accuracy = self.get_odk_values(animal_array, group_key + 'dob_type', True, 27)
                animal_dob = self.get_odk_values(animal_array, group_key + 'animal_dob', False, None)

                group_key = 'animalregistration/grp_appearance/'
                wounded = self.get_odk_values(animal_array, group_key + 'assessment_wounds', True, 1)
                wound_count = self.get_odk_values(animal_array, group_key + 'number_wounds', False, None)
                wounded_area = self.get_odk_values(animal_array, group_key + 'location_wounds', False, None)
                hair_patched = self.get_odk_values(animal_array, group_key + 'assessment_hairlosspatches', True, 1)
                hair_patches_count = self.get_odk_values(animal_array, group_key + 'number_hairlosspatches', False,
                                                         None)
                hair_patch_location = self.get_odk_values(animal_array, group_key + 'location_hairlosspatches', False,
                                                          None)

                group_key = 'animalregistration/grp_physicalexamination/'
                body_temperature = self.get_odk_values(animal_array, group_key + 'body_temperature', False, None)
                presence_of_injury_in_the_abdomen = self.get_odk_values(animal_array, group_key + 'abdomen_injurytype',
                                                                        True, 1)
                abdominal_injury_type = self.get_odk_values(animal_array, group_key + 'abdomen_injury', False, None)
                presence_of_external_parasite = self.get_odk_values(animal_array, group_key + 'external_parasite', True,
                                                                    1)
                hanging_out_of_placenta = self.get_odk_values(animal_array, group_key + 'placenta', True, 1)
                presence_of_injury_on_udder = self.get_odk_values(animal_array, group_key + 'udder_injury', True, 1)

                appearance_of_udder = self.get_odk_values(animal_array, group_key + 'udder', True, 8)
                position_of_foetus = self.get_odk_values(animal_array, group_key + 'foetus_position', True, 9)
                ease_of_handling = self.get_odk_values(animal_array, group_key + 'handling_ease', True, 18)
                colour_of_visible_mucous_membrane = self.get_odk_values(animal_array, group_key + 'mucous_membrane',
                                                                        True, 12)
                genital_discharge = self.get_odk_values(animal_array, group_key + 'genital_discharge', True, 11)
                water_bag = self.get_odk_values(animal_array, group_key + 'water_bag', True, 10)

                # Lab Tests
                group_key = 'animalregistration/grp_findings/'
                rapid_tests_done = self.get_odk_values(animal_array, group_key + 'rapidtest_done', True, 1)
                rapid_tests_1 = self.get_odk_values(animal_array, group_key + 'rapidtest_1', False, None)
                rapid_tests_2 = self.get_odk_values(animal_array, group_key + 'rapidtest_2', False, None)
                rapid_tests_3 = self.get_odk_values(animal_array, group_key + 'rapidtest_3', False, None)

                lab_test_recommended = self.get_odk_values(animal_array, group_key + 'labtest_recommended', True, 1)
                lab_tests_1 = self.get_odk_values(animal_array, group_key + 'la_recommendation1', False, None)
                lab_tests_2 = self.get_odk_values(animal_array, group_key + 'la_recommendation2', False, None)
                lab_tests_3 = self.get_odk_values(animal_array, group_key + 'la_recommendation3', False, None)

                lab_test_results = self.get_odk_values(animal_array, group_key + 'lab_results', True, 1)
                lab_test_result_1 = self.get_odk_values(animal_array, group_key + 'labresult_1', False, None)
                lab_test_result_2 = self.get_odk_values(animal_array, group_key + 'labresult_2', False, None)
                lab_test_result_3 = self.get_odk_values(animal_array, group_key + 'labresult_3', False, None)
                per_rectum_examination_findings = self.get_odk_values(animal_array, group_key + 'rectal_examination',
                                                                      False, None)

                # Treatment
                group_key = 'animalregistration/grp_treatment/'
                treated = self.get_odk_values(animal_array, group_key + 'treatment_given', True, 1)
                treatment_1 = self.get_odk_values(animal_array, group_key + 'treatment_1', False, None)
                treatment_2 = self.get_odk_values(animal_array, group_key + 'treatment_2', False, None)
                treatment_3 = self.get_odk_values(animal_array, group_key + 'treatment_3', False, None)
                advised = self.get_odk_values(animal_array, group_key + 'advice_given', True, 1)
                treatment_advice_given = self.get_odk_values(animal_array, group_key + 'advice', False, None)

                species = self.get_catalogue_item_id(21, species_code)
                animal_type = self.get_catalogue_item_id(14, animal_type_code)
                breed = self.search_for_breed_using_breed_code(breed_code)

                # Do not resolve catalogue item if the code is not set
                # Prevents -> IndexError: list index out of range
                if show_sign_of_heat_after_first_heat_code is not None:
                    show_heat = self.get_catalogue_item_id(1, show_sign_of_heat_after_first_heat_code)
                    show_heat_id = show_heat['data'][0]['id']
                else:
                    show_heat_id = None

                if type_of_mating_code is not None:
                    mating_type = self.get_catalogue_item_id(13, type_of_mating_code)
                    type_of_mating_id = mating_type['data'][0]['id']
                else:
                    type_of_mating_id = None

                if animal_conceived_code is not None:
                    animal_conceived = self.get_catalogue_item_id(1, animal_conceived_code)
                    animal_conceived_id = animal_conceived['data'][0]['id']
                else:
                    animal_conceived_id = None

                if dystocia_code is not None:
                    dystocia = self.get_catalogue_item_id(1, dystocia_code)
                    dystocia_id = dystocia['data'][0]['id']
                else:
                    dystocia_id = None

                if dystocia_foetus_status_code is not None:
                    dystocia_foetus_status = self.get_catalogue_item_id(15, dystocia_foetus_status_code)
                    dystocia_foetus_status_id = dystocia_foetus_status['data'][0]['id']
                else:
                    dystocia_foetus_status_id = None

                if delayed_post_partum_heat_code is not None:
                    delayed_post_partum_heat = self.get_catalogue_item_id(1, delayed_post_partum_heat_code)
                    delayed_post_partum_heat_id = delayed_post_partum_heat['data'][0]['id']
                else:
                    delayed_post_partum_heat_id = None

                if retention_of_placenta_code is not None:
                    retention_of_placenta = self.get_catalogue_item_id(1, retention_of_placenta_code)
                    retention_of_placenta_id = retention_of_placenta['data'][0]['id']
                else:
                    retention_of_placenta_id = None

                if abortion_code is not None:
                    abortion = self.get_catalogue_item_id(1, abortion_code)
                    abortion_id = abortion['data'][0]['id']
                else:
                    abortion_id = None

                if still_birth_code is not None:
                    still_birth = self.get_catalogue_item_id(1, still_birth_code)
                    still_birth_id = still_birth['data'][0]['id']
                else:
                    still_birth_id = None

                if mastitis_code is not None:
                    mastitis = self.get_catalogue_item_id(1, mastitis_code)
                    mastitis_id = mastitis['data'][0]['id']
                else:
                    mastitis_id = None

                if teat_canal_blockage_code is not None:
                    teat_canal_blockage = self.get_catalogue_item_id(1, teat_canal_blockage_code)
                    teat_canal_blockage_id = teat_canal_blockage['data'][0]['id']
                else:
                    teat_canal_blockage_id = None

                if lameness_history_code is not None:
                    lameness_history = self.get_catalogue_item_id(1, lameness_history_code)
                    lameness_history_id = lameness_history['data'][0]['id']
                else:
                    lameness_history_id = None

                if hip_dislocation_fracture_history_code is not None:
                    hip_dislocation_fracture_history = self.get_catalogue_item_id(1,
                                                                                  hip_dislocation_fracture_history_code)
                    hip_dislocation_fracture_history_id = hip_dislocation_fracture_history['data'][0]['id']
                else:
                    hip_dislocation_fracture_history_id = None

                if udder_fibrotic_change_status_code is not None:
                    udder_fibrotic_change_status = self.get_catalogue_item_id(16, udder_fibrotic_change_status_code)
                    udder_fibrotic_change_status_id = udder_fibrotic_change_status['data'][0]['id']
                else:
                    udder_fibrotic_change_status_id = None

                if udder_fibrotic_change_code is not None:
                    udder_fibrotic_change = self.get_catalogue_item_id(1, udder_fibrotic_change_code)
                    udder_fibrotic_change_id = udder_fibrotic_change['data'][0]['id']
                else:
                    udder_fibrotic_change_id = None

                if repeat_breeding_code is not None:
                    repeat_breeding = self.get_catalogue_item_id(1, repeat_breeding_code)
                    repeat_breeding_id = repeat_breeding['data'][0]['id']
                else:
                    repeat_breeding_id = None

                if general_appearance_code is not None:
                    general_appearance = self.get_catalogue_item_id(3, general_appearance_code)
                    general_appearance_id = general_appearance['data'][0]['id']
                else:
                    general_appearance_id = None

                if body_coat_code is not None:
                    body_coat = self.get_catalogue_item_id(4, body_coat_code)
                    body_coat_id = body_coat['data'][0]['id']
                else:
                    body_coat_id = None

                if general_health_condition_code is not None:
                    general_health_condition = self.get_catalogue_item_id(5, general_health_condition_code)
                    general_health_condition_id = general_health_condition['data'][0]['id']
                else:
                    general_health_condition_id = None

                if appetite_code is not None:
                    appetite = self.get_catalogue_item_id(6, appetite_code)
                    appetite_id = appetite['data'][0]['id']
                else:
                    appetite_id = None

                if eyes_code is not None:
                    eyes = self.get_catalogue_item_id(7, eyes_code)
                    eyes_id = eyes['data'][0]['id']
                else:
                    eyes_id = None

                species_id = species['data'][0]['id']
                animal_type_id = animal_type['data'][0]['id']
                breed_id = breed['data'][0]['id']

                payload_animal = {
                    'farmer_id': farm_id,
                    'animal_identification_number': animal_id,
                    'breed_id': breed_id,
                    'animal_dob': animal_dob,
                    'dob_accuracy': dob_accuracy,
                    'species_id': species_id,
                    'animal_type_id': animal_type_id,
                    'age_at_first_heat': age_at_first_heat,
                    'show_sign_of_heat_after_first_heat': show_heat_id,
                    'interval_btw_2_3_successive_heats': interval_btw_2_3_successive_heats,
                    'age_at_first_calving': age_at_first_calving,
                    'number_of_lactation': number_of_lactation,
                    'time_interval_btw_last_calving_to_next_heat': time_interval_btw_last_calving_to_next_heat,
                    'time_interval_btw_last_calving_to_next_conception': time_interval_btw_last_calving_to_next_conception,
                    'date_of_service': date_of_service,
                    'type_of_mating': type_of_mating_id,
                    'months_of_gestation_at_present': gestation_months,
                    'number_of_ai_per_conception': ai_conceptions,
                    'conception_after_last_service': animal_conceived_id,
                    'dystocia': dystocia_id,
                    'dystocia_foetus_status': dystocia_foetus_status_id,
                    'delayed_post_partum_heat': delayed_post_partum_heat_id,
                    'delayed_post_partum_heat_length': delayed_post_partum_heat_length,
                    'retention_of_placenta': retention_of_placenta_id,
                    'retention_of_placenta_count': retention_of_placenta_count,
                    'abortion': abortion_id,
                    'abortion_count': abortion_count,
                    'abortion_month': abortion_month,
                    'still_birth': still_birth_id,
                    'still_birth_count': still_birth_count,
                    'mastitis_quarters_affected': mastitis_quarters_affected,
                    'teat_canal_blockage': teat_canal_blockage_id,
                    'mastitis': mastitis_id,
                    'lameness_history': lameness_history_id,
                    'lameness_treatment': lameness_treatment,
                    'hip_dislocation_fracture_history': hip_dislocation_fracture_history_id,
                    'duration_of_the_existing_disease': duration_of_the_existing_disease,
                    'udder_fibrotic_change_status': udder_fibrotic_change_status_id,
                    'udder_fibrotic_change': udder_fibrotic_change_id,
                    'repeat_breeding': repeat_breeding_id,
                    'repeat_breeding_count': repeat_breeding_count,
                    'general_appearance': general_appearance_id,
                    'body_coat': body_coat_id,
                    'general_health_condition': general_health_condition_id,
                    'appetite': appetite_id,
                    'eyes': eyes_id,
                    'wounded': wounded,
                    'wound_count': wound_count,
                    'wounded_area': wounded_area,
                    'hair_patched': hair_patched,
                    'hair_patches_count': hair_patches_count,
                    'hair_patch_location': hair_patch_location,
                    'body_temperature': body_temperature,
                    'presence_of_injury_in_the_abdomen': presence_of_injury_in_the_abdomen,
                    'abdominal_injury_type': abdominal_injury_type,
                    'presence_of_external_parasite': presence_of_external_parasite,
                    'appearance_of_udder': appearance_of_udder,
                    'presence_of_injury_on_udder': presence_of_injury_on_udder,
                    'hanging_out_of_placenta': hanging_out_of_placenta,
                    'position_of_foetus': position_of_foetus,
                    'ease_of_handling': ease_of_handling,
                    'colour_of_visible_mucous_membrane': colour_of_visible_mucous_membrane,
                    'genital_discharge': genital_discharge,
                    'water_bag': water_bag,
                    'rapid_tests_done': rapid_tests_done,
                    'rapid_tests_1': rapid_tests_1,
                    'rapid_tests_2': rapid_tests_2,
                    'rapid_tests_3': rapid_tests_3,
                    'lab_test_recommended': lab_test_recommended,
                    'lab_tests_1': lab_tests_1,
                    'lab_tests_2': lab_tests_2,
                    'lab_tests_3': lab_tests_3,
                    'lab_test_results': lab_test_results,
                    'lab_test_result_1': lab_test_result_1,
                    'lab_test_result_2': lab_test_result_2,
                    'lab_test_result_3': lab_test_result_3,
                    'per_rectum_examination_findings': per_rectum_examination_findings,
                    'treated': treated,
                    'treatment_1': treatment_1,
                    'treatment_2': treatment_2,
                    'treatment_3': treatment_3,
                    'advised': advised,
                    'treatment_advice_given': treatment_advice_given
                }

                try:
                    animal = self.odoo.env[model_animal]
                    record_id = animal.create(payload_animal)
                    animal_id = record_id
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
                # Save Vaccination Records
                try:
                    vax_object = self.get_odk_values(animal_array, 'animalregistration/repeat_vaccinetype',
                                                     False, None)

                    if vax_object is not None:
                        response, record_id = self.save_vaccination_record(vax_object, animal_id)

                except Exception as e:
                    logger.exception(e)
                    response = {
                        'code': status.HTTP_400_BAD_REQUEST,
                        'status': 'error',
                        'message': str(e)
                    }

                # Save De-worming Records
                try:
                    deworm_object = self.get_odk_values(animal_array, 'animalregistration/repeat_dewormingdate',
                                                        False, None)
                    if deworm_object is not None:
                        response, record_id = self.save_deworming_record(deworm_object, animal_id)
                except Exception as e:
                    logger.exception(e)
                    response = {
                        'code': status.HTTP_400_BAD_REQUEST,
                        'status': 'error',
                        'message': str(e)
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
