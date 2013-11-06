from polls.models import Poll, Choice, AnswerSet
from django.contrib import admin

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 3

class PollAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,               {'fields': ['question']}),
    ]
    inlines = [ChoiceInline]
    
admin.site.register(Poll, PollAdmin)

class AnswerAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,               {'fields': ['name']}),
        ('Poll question', {'fields': ['question']}),
    ]
    inlines = []

admin.site.register(AnswerSet)#, AnswerAdmin)
