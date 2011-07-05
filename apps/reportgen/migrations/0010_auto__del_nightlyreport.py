# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting model 'NightlyReport'
        db.delete_table('reportgen_nightly_report')


    def backwards(self, orm):
        
        # Adding model 'NightlyReport'
        db.create_table('reportgen_nightly_report', (
            ('time_period_index', self.gf('django.db.models.fields.PositiveSmallIntegerField')(db_index=True)),
            ('report', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['reportgen.Report'], max_length=60)),
            ('updated_on', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('time_period', self.gf('django.db.models.fields.CharField')(max_length=2, db_index=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('reportgen', ['NightlyReport'])


    models = {
        'reportgen.generatedreport': {
            'Meta': {'ordering': "('title',)", 'object_name': 'GeneratedReport', 'db_table': "'reportgen_generated_report'"},
            'error_message': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'fileformat': ('django.db.models.fields.CharField', [], {'max_length': '10', 'db_index': 'True'}),
            'filename': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '255', 'blank': 'True'}),
            'finished_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'period_title': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'report': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['reportgen.Report']", 'max_length': '60'}),
            'started_at': ('django.db.models.fields.DateTimeField', [], {}),
            'task_id': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'task_progress': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'task_state': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'updated_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'variant_title': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'})
        },
        'reportgen.report': {
            'Meta': {'ordering': "('title',)", 'object_name': 'Report'},
            'classname': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'})
        }
    }

    complete_apps = ['reportgen']
