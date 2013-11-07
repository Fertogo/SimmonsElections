from django.db import models

class Poll(models.Model):
    question = models.CharField(max_length=200)
    
    def __unicode__(self):
        return self.question

class Choice(models.Model):
    poll = models.ForeignKey(Poll)
    choice = models.CharField(max_length=200)
    
    def num_first_selected(self):
        return len(AnswerSet.objects.filter(first_choice=self, active=True))
    
    def num_second_selected(self):
        return len(AnswerSet.objects.filter(second_choice=self, active=True))
    
    def num_third_selected(self):
        return len(AnswerSet.objects.filter(third_choice=self, active=True))
    
    def __unicode__(self):
        return self.choice

class AnswerSet(models.Model):
    name = models.CharField(max_length=200)
    question = models.ForeignKey(Poll)
    first_choice = models.ForeignKey(Choice, related_name='first', null=True, blank=True)
    second_choice = models.ForeignKey(Choice, related_name='second', null=True, blank=True)
    third_choice = models.ForeignKey(Choice, related_name='third', null=True, blank=True)
    active = models.BooleanField()
    created = models.DateTimeField(auto_now_add=True)
    
    def __unicode__(self):
        return self.name + " answering " + str(self.question) + " at " + str(self.created)