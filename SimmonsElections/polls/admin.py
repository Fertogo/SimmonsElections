from polls.models import Poll, Choice, AnswerSet, Resident, RawResults
from django.contrib import admin

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 3

class PollAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['question', 'role', 'order']}),
    ]
    inlines = [ChoiceInline]
    
admin.site.register(Poll, PollAdmin)

class AnswerAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['name']}),
        ('Poll question', {'fields': ['question']}),
    ]

admin.site.register(AnswerSet)#, AnswerAdmin)
admin.site.register(Resident)
admin.site.register(RawResults)
