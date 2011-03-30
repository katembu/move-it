# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting field 'Report.basename'
        db.delete_column('reportgen_report', 'basename')

        # Deleting field 'Report.updated_on'
        db.delete_column('reportgen_report', 'updated_on')


    def backwards(self, orm):
        
        # We cannot add back in field 'Report.basename'
        raise RuntimeError(
            "Cannot reverse this migration. 'Report.basename' and its values cannot be restored.")

        # We cannot add back in field 'Report.updated_on'
        raise RuntimeError(
            "Cannot reverse this migration. 'Report.updated_on' and its values cannot be restored.")


    models = {
        'reportgen.generatedreport': {
            'Meta': {'ordering': "('title',)", 'object_name': 'GeneratedReport', 'db_table': "'reportgen_generated_report'"},
            'error_message': ('django.db.models.fields.TextField', [], {}),
            'fileformat': ('django.db.models.fields.CharField', [], {'max_length': '10', 'db_index': 'True'}),
            'filename': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            'finished_at': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'period_title': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'started_at': ('django.db.models.fields.DateTimeField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'updated_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'variant_title': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'})
        },
        'reportgen.nightlyreport': {
            'Meta': {'ordering': "('report__title',)", 'object_name': 'NightlyReport', 'db_table': "'reportgen_nightly_report'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'report': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['reportgen.Report']", 'max_length': '60'}),
            'time_period': ('django.db.models.fields.CharField', [], {'max_length': '2', 'db_index': 'True'}),
            'time_period_index': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'}),
            'updated_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'reportgen.report': {
            'Meta': {'ordering': "('title',)", 'object_name': 'Report'},
            'classname': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        }
    }

    complete_apps = ['reportgen']
