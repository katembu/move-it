'''
Household Visit Report
'''

from django.db import connection

from django.utils.translation import ugettext as _

from indicator import Indicator
from indicator import DifferenceIndicator 
from indicator import Percentage
from indicator import QuerySetType

from childcount.models import Patient
from childcount.models.reports import HouseholdVisitReport

class Total(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "total"
    short_name  = _("HH Visits")
    long_name   = _("Total number of household visits")

    @classmethod
    def _value(cls, period, data_in):
        return HouseholdVisitReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=\
                    (period.start, period.end))\
            .count()

class Unique(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "unique"
    short_name  = _("Uniq. HH Visits")
    long_name   = _("Total number of visits to unique households")

    @classmethod
    def _value(cls, period, data_in):
        return HouseholdVisitReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=\
                    (period.start, period.end))\
            .values('encounter__patient')\
            .distinct()\
            .count()

class OnTime(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "on_time"
    short_name  = _("On-Time HH Visits")
    long_name   = _("Number of unique households getting "\
                    "a visit in the last 90 days and also in the 90 "\
                    "days before their last visit.")

    @classmethod
    def _value(cls, period, data_in):
        pks = ','.join([str(patient.pk) for patient in data_in])
        date_start = period.start.strftime('%Y-%m-%d %H:%M:%S')
        date_end   = period.end.strftime('%Y-%m-%d %H:%M:%S')
       
        cursor = connection.cursor()
        #cursor.execute(\
        q='''
        /* Get the total number of rows */
        SELECT 
            COUNT(*)
        FROM
            /* This SELECT has one row for every household we want to count...
                That is, it's one row for every household that has been visited
                on time. */
            (SELECT
                `latest_visits`.`patient_id`,
                `latest_visits`.`cur_date`
                /* MIN(DATEDIFF(`latest_visits`.`cur_date`, `cc_encounter2`.`encounter_date`))*/

            FROM
                /* This sub-query gets the latest household visit for each household */
                (SELECT
                    `cc_patient`.`id` AS `patient_id`,
                    `cc_patient`.`created_on` AS `created_on`,
                    GREATEST(`cc_patient`.`created_on`, MAX(`cc_encounter`.`encounter_date`)) AS `cur_date`

                FROM `cc_patient`

                LEFT JOIN `cc_encounter`
                    ON (`cc_patient`.`id`=`cc_encounter`.`patient_id`   
                        AND `cc_encounter`.`encounter_date` BETWEEN "%(date_start)s" AND "%(date_end)s")
                LEFT JOIN `cc_ccrpt`
                    ON (`cc_encounter`.`id`=`cc_ccrpt`.`encounter_id`)
                INNER JOIN `cc_hhvisitrpt`
                    ON (`cc_ccrpt`.`id`=`cc_hhvisitrpt`.`ccreport_ptr_id`)

                GROUP BY `cc_patient`.`id`) AS `latest_visits`

            LEFT JOIN `cc_encounter`      AS `cc_encounter2`
                ON (`latest_visits`.`patient_id`=`cc_encounter2`.`patient_id` 
                    AND `latest_visits`.`cur_date` > `cc_encounter2`.`encounter_date`)
            LEFT JOIN `cc_ccrpt`          AS `cc_ccrpt2` 
                ON (`cc_encounter2`.`id`=`cc_ccrpt2`.`encounter_id`)
            INNER JOIN `cc_hhvisitrpt`    AS `cc_hhvisitrpt2` 
                ON (`cc_ccrpt2`.`id`=`cc_hhvisitrpt2`.`ccreport_ptr_id`)

            WHERE

                /* The difference between the latest visit and the second-latest visit should
                    be between 0 and 90 days... If there's no second-latest visit, we consider
                    the registration date instead. */
                DATEDIFF(`latest_visits`.`cur_date`, 
                    GREATEST(`latest_visits`.`created_on`, `cc_encounter2`.`encounter_date`)) < 90 AND
                DATEDIFF(`latest_visits`.`cur_date`, 
                    GREATEST(`latest_visits`.`created_on`, `cc_encounter2`.`encounter_date`)) > 0 AND
                `latest_visits`.`patient_id` IN (%(patient_pks)s) AND
                `latest_visits`.`cur_date` BETWEEN "%(date_start)s" AND "%(date_end)s"

            GROUP BY `patient_id`) as `unique_otv`
        ''' % {'patient_pks' : pks, 
                'date_start': date_start, 
                'date_end': date_end}

        cursor.execute(q)
        return int(cursor.fetchone()[0])

class Late(DifferenceIndicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "late"
    short_name  = _("Late HH Visits")
    long_name   = _("Total number of late visits to unique households")

    cls_first   = Total
    cls_second  = OnTime
