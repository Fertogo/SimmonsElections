from django.shortcuts import render_to_response, get_object_or_404, render
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.template import RequestContext
from polls.models import Choice, Poll, AnswerSet

try:
    import subprocess
    import ldap
    import ldap.filter

    from django.contrib.auth.middleware import RemoteUserMiddleware
    from django.contrib.auth.backends import RemoteUserBackend
    from django.contrib.auth.views import login
    from django.contrib.auth import REDIRECT_FIELD_NAME
    from django.http import HttpResponseRedirect
    from django.contrib import auth
    from django.core.exceptions import ObjectDoesNotExist
    import settings
    importedLdap = True
except ImportError, exp:
    importedLdap = False

kerb = "cosmosd"

def index(request):
    kerb = str(importedLdap)
    if importedLdap:
        kerb = "rawr"
    latest_poll_list = Poll.objects.all()
    answers_so_far = AnswerSet.objects.all().filter(active=True)
    for poll in latest_poll_list:
        try:
            answer_to_poll = answers_so_far.get(question=poll.id, name=kerb, active=True)
            poll.answer = answer_to_poll
        except (AnswerSet.DoesNotExist):
            poll.answer = None
    return render_to_response('polls/index.html', {'latest_poll_list': latest_poll_list, 'kerb': kerb})

def vote(request, poll_id):
    p = get_object_or_404(Poll, pk=poll_id)
    try:
        choice_text = request.POST['choice_num']
        choice_num = int(choice_text)
        #kerb = request.POST['kerb']
        selected_choice = p.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the poll voting form.
        try:
            if choice_num == 1:
                answer = AnswerSet(name=kerb, question=p, active=True)
            else:
                answer = AnswerSet.objects.get(name=kerb, question=p, active=True)
        except AnswerSet.DoesNotExist:
            answer = AnswerSet(name=kerb, question=p, active=True)
        return render_to_response('polls/detail.html', {
            'poll': p,
            'error_message': "You didn't select a choice.",
            'previous_1': answer.first_choice,
            'previous_2': answer.second_choice,
            'previous_3': answer.third_choice,
        }, context_instance=RequestContext(request))
    else:
        new_answer = False
        try:
            answer = AnswerSet.objects.get(name=kerb, question=p, active=True)
        except AnswerSet.DoesNotExist:
            answer = AnswerSet(name=kerb, question=p, active=True)
            new_answer = True
        if choice_num == 1 and not new_answer:
            answer.active = False
            answer.save()
            answer = AnswerSet(name=kerb, question=p, active=True)
        valid_choices = [1, 2, 3]
        max_choice = 3
        if choice_num in valid_choices:
            if choice_num == 1:
                answer.first_choice = selected_choice
            elif choice_num == 2:
                answer.second_choice = selected_choice
            elif choice_num == 3:
                answer.third_choice = selected_choice
            
            if answer.first_choice and answer.second_choice and (answer.first_choice == answer.second_choice or (answer.third_choice and (answer.second_choice == answer.third_choice or answer.first_choice == answer.third_choice))):
                return render_to_response('polls/detail.html', {
                    'poll': p,
                    'error_message': "Your choices match somehow. Please reselect your choices.",
                }, context_instance=RequestContext(request))

            answer.save()
            if choice_num == max_choice or choice_num == len(p.choice_set.all()):
                # done picking
                #return HttpResponseRedirect(reverse('poll_list'))
                return render_to_response('polls/confirm.html', {
                    'poll': p,
                    'previous_1': answer.first_choice,
                    'previous_2': answer.second_choice,
                    'previous_3': answer.third_choice,
                }, context_instance=RequestContext(request))
            else:
                # go to next choice
                return render_to_response('polls/detail.html', {
                    'poll': p,
                    'choice_num': str(choice_num + 1),
                    'previous_1': answer.first_choice,
                    'previous_2': answer.second_choice,
                    'previous_3': answer.third_choice,
                }, context_instance=RequestContext(request))
        else:
            # choice num is not valid
            return render_to_response('polls/detail.html', {
                'poll': p,
                'error_message': "Stop messing with the form.",
            }, context_instance=RequestContext(request))
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
