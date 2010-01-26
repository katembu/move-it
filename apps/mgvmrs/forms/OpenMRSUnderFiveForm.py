#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: rgaudin

from mgvmrs.forms.OpenMRSFormInterface import *


class OpenMRSUnderFiveForm(OpenMRSFormInterface):

    ''' Children Under 5 Encounter Form

    Matchs OpenMRS Form #57
    Last Updated: Jan 15 2010 - rgaudin '''

    template_name = 'OpenMRSUnderFiveForm.xml'

    # concepts
    YES = '1065^YES^99DCT'
    NO = '1066^NO^99DCT'
    UNKNOWN = '1067^UNKNOWN^99DCT'
    POSITIVE = '703^POSITIVE^99DCT'
    NEGATIVE = '664^NEGATIVE^99DCT'
    INDETERMINATE = '1138^INDETERMINATE^99DCT'

    TEST_ORDER_MALARIA = '1643^RAPID TEST FOR MALARIA^99DCT'
    TEST_ORDER_NONE = '1107^NONE^99DCT'
    TEST_MALARIA_RDT_INDETERMINATE = '1138^INDETERMINATE^99DCT'

    MEDIC_ORDER_ZINC = '86672^Zinc^99DCT'
    MEDIC_ORDER_ORS = '351^ORAL REHYDRATION SALTS^99DCT'

    CURRENT_MEDIC_ORDER_ANTIMALARIAL = '5839^ANTIMALARIAL MEDICATIONS^99DCT'
    CURRENT_MEDIC_ORDER_ANTIBIOTIC = '1195^ANTIBIOTICS^99DCT'
    CURRENT_MEDIC_ORDER_ANTIPYRETIC = '1881^Antipyretic Medications^99DCT'

    REFERRAL_EMERGENCY = '1882^Emergency (status)^99DCT'
    REFERRAL_NON_CODED = '5622^OTHER NON-CODED^99DCT'
    REFERRAL_URGENT = '1883^Urgent (status)^99DCT'
    REFERRAL_WHEN_CONVENIENT = '1884^When Convenient status)^99DCT'

    # answers group
    A_YESNO = (YES, NO, UNKNOWN)
    A_POSIT = (POSITIVE, NEGATIVE, INDETERMINATE)

    # Allowed answers
    # (TYPE, LIST OF VALUES, DEFAULT)
    fields = {
        'calculated_age': (OpenMRSFormInterface.T_NM, None, None),
        'number_of_days_since_birth': (OpenMRSFormInterface.T_NM, None, None),
        'bacille_camile_guerin_vaccination': (OpenMRSFormInterface.T_CWE, \
                                              A_YESNO, UNKNOWN),
        'danger_signs_present': (OpenMRSFormInterface.T_CWE, A_YESNO, UNKNOWN),
        'breastfed_exclusively': (OpenMRSFormInterface.T_CWE, \
                                  A_YESNO, UNKNOWN),
        'danger_signs_present_1': (OpenMRSFormInterface.T_CWE, \
                                   A_YESNO, UNKNOWN),
        'fever': (OpenMRSFormInterface.T_CWE, A_YESNO, UNKNOWN),
        'diarrhea': (OpenMRSFormInterface.T_CWE, A_YESNO, UNKNOWN),
        'danger_signs_present_2': (OpenMRSFormInterface.T_CWE, \
                                   A_YESNO, UNKNOWN),
        'mid_upper_arm_circumference': (OpenMRSFormInterface.T_NM, None, None),
        'oedema': (OpenMRSFormInterface.T_CWE, A_YESNO, UNKNOWN),
        'tests_ordered': (OpenMRSFormInterface.T_CWE, \
                          (TEST_ORDER_MALARIA, TEST_ORDER_NONE), None),
        'rapid_test_for_malaria': (OpenMRSFormInterface.T_CWE, A_POSIT, None),
        'dyspnea': (OpenMRSFormInterface.T_CWE, A_YESNO, UNKNOWN),
        'referral_priority': (OpenMRSFormInterface.T_CWE, \
                              (REFERRAL_EMERGENCY, REFERRAL_NON_CODED, \
                               UNKNOWN, REFERRAL_URGENT, \
                               REFERRAL_WHEN_CONVENIENT), None),
        'current_medication_order_1': (OpenMRSFormInterface.T_ZZ, \
                                       (MEDIC_ORDER_ORS, \
                                        MEDIC_ORDER_ZINC), None),
        'current_medication_order': (OpenMRSFormInterface.T_ZZ, \
                                     (CURRENT_MEDIC_ORDER_ANTIMALARIAL, \
                                      CURRENT_MEDIC_ORDER_ANTIBIOTIC, \
                                      CURRENT_MEDIC_ORDER_ANTIPYRETIC), None),
    }

    values = {}
