from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.template import RequestContext
from polls.models import Choice, Poll, AnswerSet

def vote(request, poll_id):
    p = get_object_or_404(Poll, pk=poll_id)
    try:
        selected_choice = p.choice_set.get(pk=request.POST['choice'])
        choice_text = request.POST['choice_num']
        choice_num = int(choice_text)
        kerb = request.POST['kerb']
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the poll voting form.
        try:
            answer = AnswerSet.objects.get(name=kerb, question=p)
        except AnswerSet.DoesNotExist:
            answer = AnswerSet(name=kerb, question=p)
        return render_to_response('polls/detail.html', {
            'poll': p,
            'error_message': "You didn't select a choice.",
            'previous_1': answer.first_choice,
            'previous_2': answer.second_choice,
            'previous_3': answer.third_choice,
        }, context_instance=RequestContext(request))
    else:
        try:
            answer = AnswerSet.objects.get(name=kerb, question=p)
        except AnswerSet.DoesNotExist:
            answer = AnswerSet(name=kerb, question=p)
        if choice_num == 1:
            answer.first_choice = None
            answer.second_choice = None
            answer.third_choice = None
        valid_choices = [1, 2, 3]
        max_choice = 3
        if choice_num in valid_choices:
            if choice_num == 1:
                answer.first_choice = selected_choice
            elif choice_num == 2:
                answer.second_choice = selected_choice
            elif choice_num == 3:
                answer.third_choice = selected_choice

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
