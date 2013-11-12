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
from polls.models import Choice, Poll, AnswerSet, Resident
from mit import ScriptsRemoteUserBackend

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

@login_required(login_url=reverse_lazy('polls_login'))
def index(request, **kwargs):
    kerb = str(request.user)
    kerb_obscured = obscure_str(request.user)
    latest_poll_list = Poll.objects.all().order_by('question')
    answers_so_far = AnswerSet.objects.all().filter(active=True)
    for poll in latest_poll_list:
        try:
            answer_to_poll = answers_so_far.get(question=poll.id, name=kerb_obscured, active=True)
            if answer_to_poll.nonempty():
                poll.answer = answer_to_poll
            else:
                poll.answer = None
        except (AnswerSet.DoesNotExist):
            poll.answer = None
    return render_to_response('polls/index.html', {'latest_poll_list': latest_poll_list, 'user': request.user})

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
            return HttpResponse('Invalid login -- actions are logged. Be aware that only the most recent link works for email-based login.')
    else:
        global importedLdap
        if importedLdap:
            return mit.scripts_login(request, template_name='polls/login_fail.html')
        else:
            return render_to_response('polls/login_fail.html', {'error_message': 'Ldap not installed. Contact simmons-nominations@mit.edu with this error message please.'})
        return HttpResponseRedirect(reverse('poll_list'))

def login_email(request):
    if 'email' not in request.POST:
        return HttpResponseRedirect(reverse('poll_list'))
    kerb = request.POST['email']
    if kerb[-8:].lower() == '@mit.edu':
        kerb = kerb[:-8]
    if Resident.objects.filter(athena=kerb).count() == 0:
        return render_to_response('polls/login_fail.html', {'email_error': kerb + ' is not a Simmons resident email! If you think it is, email simmons-nominations@mit.edu.'}, context_instance=RequestContext(request))
    password = User.objects.make_random_password(length=20)
    user, created = User.objects.get_or_create(username=kerb)
    scripts_remote_backend = ScriptsRemoteUserBackend()
    scripts_remote_backend.configure_user(user)
    user.set_password(password)
    user.save()
    send_mail('Simmons Elections login info', 'To vote in the Simmons elections, log in through this link.\n\nhttp://simmons-hall.scripts.mit.edu/elections/polls/login?kerberos=' + kerb + "&key=" + password + '\n\n If you need to log in again, you should go to this link again or request another link.', 
    'simmons-nominations@mit.edu', [kerb + '@mit.edu'], fail_silently=False)
    return HttpResponse('Please check your email for futher voting instructions. You may close this window.')

###
# Responses for various form displays

def form_choice_response(request, poll, kerb, answer, next_choice_num):
    logger.debug(kerb + " - Displaying form - " + poll.question + " - choice " + str(next_choice_num))
    return render_to_response('polls/detail.html', {
        'poll': poll,
        'candidates' : poll.choice_set.order_by('choice'),
        'answer': answer,
        'choice_num': next_choice_num,
        'kerb': kerb}, context_instance=RequestContext(request))

def form_error_response(request, poll, kerb, answer, error_message, next_choice_num = 1):
    return render_to_response('polls/detail.html', {
        'poll': poll,
        'candidates' : poll.choice_set.order_by('choice'),        
        'answer': answer,
        'choice_num': next_choice_num,
        'error_message': error_message,
        'kerb': kerb}, context_instance=RequestContext(request))

def form_completion_response(request, poll, kerb, answer):
    logger.debug(kerb + " - Displaying form completion - " + poll.question)
    return render_to_response('polls/confirm.html', {
        'poll': poll,
        'answer': answer,
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
        return form_choice_response(request, poll=poll, kerb=kerb, answer=answer, next_choice_num = 1)
    try:
        choice_num = int(request.POST['choice_num'])
    except:
        # choice_num not a string
        logger.warn(kerb + " - Invalid choice num - " + poll.question + ": " + request.POST['choice_num'])
        return form_error_response(request, poll=poll, kerb=kerb, answer=answer,
                                   error_message="Invalid choice_num -- actions are logged: " +
                                   "stop messing with the form.")
    if choice_num not in [1,2,3]:
        # Invalid choice number
        logger.warn(kerb + " - Invalid choice num - " + poll.question + ": " + request.POST['choice_num'])        
        return form_error_response(request, poll=poll, kerb=kerb, answer=answer,
                                   error_message="Invalid choice_num -- actions are logged: " +
                                   "stop messing with the form.")
    #####
    # Get and validate the selected choice
    try:
        selected_choice = poll.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        # No choice corresponding to selection. Redisplay form
        # Invalid choice number
        logger.warn(kerb + " - Invalid choice - " + poll.question + ": " + request.POST['choice'])                
        return form_error_response(request, poll=poll, kerb=kerb, answer=answer,
                                   next_choice_num = choice_num,                                   
                                   error_message="Invalid choice -- actions are logged: " +
                                   "stop messing with the form.")

    #####
    # Submitting a new response for choice 1 will disable the previous submission and
    # start a new submission
    if choice_num == 1 and answer.nonempty():
        answer.active = False
        answer.save()
        answer = AnswerSet(name=kerb_obscured, question=poll, active=True)

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
    # TODO
    logger.debug(kerb + " - Saving ballot - " + poll.question + ": " + str(answer.signature()))
        
    #####
    # Save changes
    answer.save()

    ####
    # Determine and display response
    if choice_num == MAX_CHOICES or choice_num == len(poll.choice_set.all()):
        return form_completion_response(request, poll=poll, kerb=kerb, answer=answer)
    else:
        return form_choice_response(request, poll=poll, kerb=kerb, answer=answer,
                                    next_choice_num = choice_num + 1)

def results(request):
    kerb = str(request.user)
    if kerb not in ['larsj', 'apark93']:
        raise Http404
    logger.debug(kerb + " - Displaying results")
    response_data = {}
    answers = AnswerSet.objects.filter(active=True)
    for answer in answers:
        if not answer.nonempty():
            continue
        question = answer.question.question
        if question not in response_data:
            response_data[question] = []
        ballot = {}
        ballot['name'] = answer.name
        ballot['choices'] = [str(answer.first_choice),
                             str(answer.second_choice),
                             str(answer.third_choice)]
        response_data[question].append(ballot)
    return HttpResponse(json.dumps(response_data, sort_keys=True, indent=4),
                        content_type="application/json")
def election_index(request):
    return render_to_response('polls/elections-index.html')

def election_index_redirect(request):
        return HttpResponseRedirect(reverse('election_index'))

def polls_index_redirect(request):
        return HttpResponseRedirect(reverse('poll_list'))    

