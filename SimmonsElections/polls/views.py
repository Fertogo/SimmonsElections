STATUS = {'polls_open': 0,
          'polls_closed': 1,
          'results': 2,
          'before': 3}
current_status = STATUS['polls_open']
deployed = False

from django.shortcuts import render_to_response, get_object_or_404, render
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse, reverse_lazy
from django.template import RequestContext
from django.core.mail import send_mail
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import auth
from django.contrib.auth import REDIRECT_FIELD_NAME, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.middleware import RemoteUserMiddleware
from django.contrib.auth.backends import RemoteUserBackend
from django.contrib.auth import login as django_login
from django.contrib.auth.models import User
from polls.models import Choice, Poll, AnswerSet, Resident, RawResults
from django.http import Http404

try:
    from mit import ScriptsRemoteUserBackend
except ImportError, exp:
    pass
    

from obscure import obscure_str
import json

import logging
logger = logging.getLogger(__name__)

try:
    import subprocess
    import ldap
    import ldap.filter

    import mit
    importedLdap = True
except ImportError, exp:
    importedLdap = False

def index(request, **kwargs):
    if deployed and not current_status == STATUS['polls_open']:
        return return_404()
    kerb = str(request.user)
    kerb_obscured = obscure_str(request.user)
    latest_poll_list = Poll.objects.all().order_by('order', 'question')
    answers_so_far = AnswerSet.objects.all().filter(active=True)
    poll_list = []
    for poll in latest_poll_list:
        poll_obj = {'poll': poll}
        if kerb in ['larsj', 'apark93', 'skyler', 'kipnissn']:
            poll_obj['count'] = AnswerSet.objects.filter(active=True, question=poll.id).count()
        try:
            answer_to_poll = answers_so_far.get(question=poll.id, name=kerb_obscured, active=True)
            if answer_to_poll.nonempty():
                poll_obj['answer'] = answer_to_poll
            else:
                poll_obj['answer'] = None
        except (AnswerSet.DoesNotExist):
            poll_obj['answer'] = None
        poll_obj['choices'] = []
        for choice in poll.choice_set.order_by('choice'):
            choice_obj = {}
            choice_obj['choice'] = choice
            if poll_obj['answer']:
                for i in range(1, 4):
                    if poll_obj['answer'].get_choice(i) == choice:
                        choice_obj['rank'] = i
            poll_obj['choices'].append(choice_obj)
        poll_list.append(poll_obj)
    return render_to_response('polls/index.html', {'poll_list': poll_list, 'user': request.user})

#@login_required(login_url=reverse_lazy('polls_closed'))
def results_index(request, **kwargs):
    if deployed and not current_status == STATUS['results']:
        return return_404()
    latest_poll_list = Poll.objects.all().order_by('order', 'question')
    answers_so_far = AnswerSet.objects.all().filter(active=True)
    poll_list = []

    for poll in latest_poll_list:
        poll_obj = {'poll': poll}
        poll_obj['choices'] = poll.choice_set.order_by('rank')
        poll_list.append(poll_obj)
    return render_to_response('polls/results_index.html', {'poll_list': poll_list})


def login(request):
    if 'kerberos' in request.GET and 'key' in request.GET:
        kerb = str(request.GET['kerberos'])
        pw = str(request.GET['key'])
        user = authenticate(username=kerb, password=pw)
        if user is not None:
            if user.is_active:
                django_login(request, user)
                return HttpResponseRedirect(reverse('poll_list'))
            else:
                return HttpResponse('Your account has been disabled. Contact simmons-nominations@mit.edu for help.')
        else:
            logger.debug(kerb + " - Invalid pw key: " + pw)
            return render_to_response('polls/simple-message.html', {'message': 'Invalid login -- actions are logged. Be aware that only the most recent link works for email-based login.'})            
    else:
        global importedLdap
        if importedLdap:
            return mit.scripts_login(request, template_name='polls/login_fail_new.html')
        else:
            return render_to_response('polls/login_fail_new.html', {'error_message': 'Ldap not installed. Contact simmons-nominations@mit.edu with this error message please.'})
        return HttpResponseRedirect(reverse('poll_list'))

def login_email(request):
    if 'email' not in request.POST:
        return HttpResponseRedirect(reverse('poll_list'))
    kerb = request.POST['email']
    if kerb[-8:].lower() == '@mit.edu':
        kerb = kerb[:-8]
    if Resident.objects.filter(athena=kerb).count() == 0:
        return render_to_response('polls/login_fail_new.html', {'email_error': kerb + ' is not a Simmons resident email! If you think it is, email simmons-nominations@mit.edu.'}, context_instance=RequestContext(request))
    password = User.objects.make_random_password(length=20)
    user, created = User.objects.get_or_create(username=kerb)
    scripts_remote_backend = ScriptsRemoteUserBackend()
    scripts_remote_backend.configure_user(user)
    user.set_password(password)
    user.save()
    send_mail('Simmons Elections login info', 'To vote in the Simmons elections, log in through this link.\n\nhttp://simmons-hall.scripts.mit.edu/elections/polls/login?kerberos=' + kerb + "&key=" + password + '\n\n If you need to log in again, you should go to this link again or request another link.', 
    'simmons-nominations@mit.edu', [kerb + '@mit.edu'], fail_silently=False)
    return render_to_response('polls/simple-message.html', {'message': 'Please check your email for futher voting instructions. You may close this window.', 'hide_home': True})

###
# Responses for various form displays

def get_candidates_and_rank(poll, answer):
    candidates = []
    for choice in poll.choice_set.order_by('choice'):
        choice_obj = {}
        choice_obj['choice'] = choice
        if answer:
            for i in range(1, 4):
                if answer.get_choice(i) == choice:
                    choice_obj['rank'] = i
        candidates.append(choice_obj)
    return candidates

def form_choice_response(request, poll, kerb, answer, next_choice_num):
    logger.debug(kerb + " - Displaying form - " + poll.question + " - choice " + str(next_choice_num))
    poll.choice_set.order_by('choice'),
    return render_to_response('polls/poll.html', {
        'poll': poll,
        'candidates' : get_candidates_and_rank(poll, answer),
        'answer': answer,
        'next_choice_num': next_choice_num,
        'kerb': kerb}, context_instance=RequestContext(request))

def form_error_response(request, poll, kerb, answer, error_message, next_choice_num = 4):
    return render_to_response('polls/poll.html', {
        'poll': poll,
        'candidates' : get_candidates_and_rank(poll, answer),
        'answer': answer,
        'next_choice_num': next_choice_num,
        'error_message': error_message,
        'kerb': kerb}, context_instance=RequestContext(request))
        
@login_required(login_url=reverse_lazy('polls_login'))
def vote(request, poll_id):
    MAX_CHOICES = 3
    
    kerb = str(request.user)
    kerb_obscured = obscure_str(request.user)
    poll = get_object_or_404(Poll, pk=poll_id)

    #####
    # Get or create the answer set
    # Allows the form to display the user's previous responses
    (answer, answer_created) = AnswerSet.objects.get_or_create(name=kerb_obscured, question=poll, active=True)

    #####
    # Process and validate choice num
    # If the user has not submitting any choices, choice_num will not be set
    if 'choice_num' not in request.POST:
        if answer.nonempty():
            # Choice exists, as if we've already selected everyone. A choice num of 4 will not create any
            # links to submit the form. It signifies to the template that the answer is done.
            next_choice_num = 4
        else:
            # First time, first choice is 1.
            next_choice_num = 1
        return form_choice_response(request, poll=poll, kerb=kerb, answer=answer, next_choice_num=next_choice_num)
    try:
        choice_num = int(request.POST['choice_num'])
    except:
        # choice_num not a string
        logger.warn(kerb + " - Invalid choice num - " + poll.question + ": " + request.POST['choice_num'])
        return form_error_response(request, poll=poll, kerb=kerb, answer=answer,
                                   error_message="Invalid choice_num -- actions are logged: " +
                                   "stop messing with the form.")

    ## Choice_num == 0 means clear the answer set, other choice_num involve changing the choices
    if choice_num == 0:
        if answer.nonempty():
            new_answer = AnswerSet(name=kerb_obscured, question=poll, active=True)
            answer.active = False
            answer.save()
            new_answer.save()
            answer = new_answer
        return form_choice_response(request, poll=poll, kerb=kerb, answer=answer, next_choice_num=1)
    elif choice_num not in [1,2,3]:
        # Invalid choice number
        logger.warn(kerb + " - Invalid choice num - " + poll.question + ": " + request.POST['choice_num'])        
        return form_error_response(request, poll=poll, kerb=kerb, answer=answer,
                                   error_message="Invalid choice_num -- actions are logged: " +
                                   "stop messing with the form.",
                                   next_choice_num = 4)
    #####
    # Get and validate the selected choice
    try:
        selected_choice = poll.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist, ValueError):
        # No choice corresponding to selection. Redisplay form
        # Invalid choice number
        logger.warn(kerb + " - Invalid choice - " + poll.question + ": " + request.POST['choice'])                
        return form_error_response(request, poll=poll, kerb=kerb, answer=answer,
                                   next_choice_num = choice_num,                                   
                                   error_message="Invalid choice -- actions are logged: " +
                                   "stop messing with the form.")

    #####
    # Update answer fields
    if choice_num == 1:
        answer.first_choice = selected_choice
    elif choice_num == 2:
        answer.second_choice = selected_choice
    elif choice_num == 3:
        answer.third_choice = selected_choice

    #####
    # Abandon if invalid
    if not answer.is_valid():
        logger.warn(kerb + " - Invalid ballot - " + poll.question + ": " + str(answer.signature()))
        (answer, answer_created) = AnswerSet.objects.get_or_create(name=kerb_obscured, question=poll, active=True)
        return form_error_response(request, poll=poll, kerb=kerb, answer=answer,
                                   next_choice_num = choice_num,
                                   error_message="Invalid ballot -- actions are logged: " +
                                   "stop messing with the form.")
    
    #####
    # Save logging information
    logger.debug(kerb + " - Saving ballot - " + poll.question + ": " + str(answer.signature()))
        
    #####
    # Save changes
    answer.save()

    ####
    # Determine and display response
    return form_choice_response(request, poll=poll, kerb=kerb, answer=answer,
                                next_choice_num = choice_num + 1)

def raw_results(request, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)                                                                                                               
    results = RawResults.objects.get(poll=poll)
    rawtext = results.rawtext.replace('\n', '<br />')
    return render_to_response('polls/raw_results.html',
                              {'poll': poll,
                               'text': rawtext})

def election_index(request):
    if deployed and not current_status == STATUS['before']:
        return return_404()
    return render_to_response('polls/elections-index.html')

def polls_closed(request):
    if deployed and not current_status == STATUS['polls_closed']:
        return return_404()
    return render_to_response('polls/polls-closed.html')

def return_404():
    return render_to_response('404.html')

def polls_index_redirect(request):
    if current_status == STATUS['polls_open']:
        return HttpResponseRedirect(reverse('index'))
    elif current_status == STATUS['polls_closed']:
        return HttpResponseRedirect(reverse('polls_closed'))
    elif current_status == STATUS['results']:
        return HttpResponseRedirect(reverse('results_index'))
    elif current_status == STATUS['before']:
        return HttpResponseRedirect(reverse('election_index'))
