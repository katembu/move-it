# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'NightlyReport'
        db.create_table('reportgen_nightly_report', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('report', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['reportgen.Report'], max_length=60)),
            ('time_period', self.gf('django.db.models.fields.CharField')(max_length=2, db_index=True)),
            ('time_period_index', self.gf('django.db.models.fields.PositiveSmallIntegerField')(db_index=True)),
            ('updated_on', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('reportgen', ['NightlyReport'])

        # Adding model 'Report'
        db.create_table('reportgen_report', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('basename', self.gf('django.db.models.fields.CharField')(unique=True, max_length=40, db_index=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=60, db_index=True)),
            ('classname', self.gf('django.db.models.fields.CharField')(unique=True, max_length=60, db_index=True)),
            ('updated_on', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('reportgen', ['Report'])

        # Adding model 'GeneratedReport'
        db.create_table('reportgen_generated_report', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('filename', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255, db_index=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('fileformat', self.gf('django.db.models.fields.CharField')(max_length=10, db_index=True)),
            ('period_title', self.gf('django.db.models.fields.CharField')(max_length=100, db_index=True)),
            ('variant_title', self.gf('django.db.models.fields.CharField')(max_length=100, db_index=True)),
            ('started_at', self.gf('django.db.models.fields.DateTimeField')()),
            ('finished_at', self.gf('django.db.models.fields.DateTimeField')()),
            ('error_message', self.gf('django.db.models.fields.TextField')()),
            ('updated_on', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('reportgen', ['GeneratedReport'])


    def backwards(self, orm):
        
        # Deleting model 'NightlyReport'
        db.delete_table('reportgen_nightly_report')

        # Deleting model 'Report'
        db.delete_table('reportgen_report')

        # Deleting model 'GeneratedReport'
        db.delete_table('reportgen_generated_report')


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
            'basename': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            'classname': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'db_index': 'True'}),
            'updated_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['reportgen']
