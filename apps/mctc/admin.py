from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from models.general import Zone, Facility, Case, Provider, User 
from models.logs import MessageLog, EventLog, SystemErrorLog
from models.reports import Observation
from django.utils.translation import ugettext_lazy as _

 
class ProviderInline (admin.TabularInline):
    """Allows editing Users in admin interface style"""
    model   = Provider
    fk_name = 'user'
    max_num = 1

class ProviderAdmin (UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {'fields': ('is_staff', 'is_active', 'is_superuser')}),
        (_('Groups'), {'fields': ('groups',)}),
    )
    #list_display = ("get_name_display","clinic", "mobile")
    inlines     = (ProviderInline,)
    search_fields = ['first_name']
    list_filter = ['is_active']

try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass
admin.site.register(User, ProviderAdmin)

class CaseAdmin(admin.ModelAdmin):
    list_display = ("ref_id", "first_name", "last_name", "gender", "dob","location","created_at","reporter", "age","eligible_for_measles")
    search_fields = ['ref_id', 'first_name', 'last_name']
    list_filter = ("dob",'status')
    ordering = ('-dob',)

class TheProviderAdmin(admin.ModelAdmin):
    list_display = ("get_name_display","clinic", "mobile", 'user', "role","alerts")
    list_filter = ("clinic","role")
    search_fields = ['user__first_name', 'user__last_name', 'user__username']
    
admin.site.register(Case, CaseAdmin)
admin.site.register(Provider,TheProviderAdmin)
admin.site.register(Zone)
admin.site.register(Facility)

class MessageLogAdmin(admin.ModelAdmin):
    list_display = ("sent_by_name","provider_clinic","mobile", "text", "created_at", "was_handled")
    list_filter = ("was_handled","sent_by")
    search_fields = ['mobile', 'text', ]
    
admin.site.register(MessageLog, MessageLogAdmin)

class EventLogAdmin(admin.ModelAdmin):
    list_display = ("__unicode__",)
    list_filter = ("message", "content_type")
    
admin.site.register(EventLog, EventLogAdmin)

class SystemErrorLogAdmin(admin.ModelAdmin):
    list_display = ("__unicode__",)
    list_filter = ("message", "created_at")
    
admin.site.register(SystemErrorLog, SystemErrorLogAdmin)


admin.site.register(Observation)