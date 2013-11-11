from django.shortcuts import render_to_response, get_object_or_404, render
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse, reverse_lazy
from django.template import RequestContext
from polls.models import Choice, Poll, AnswerSet, Resident
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
import string
import random

import logging
logger = logging.getLogger(__name__)

try:
    import subprocess
    import ldap
    import ldap.filter

    from django.contrib import auth
    from django.contrib.auth.middleware import RemoteUserMiddleware
    from django.contrib.auth.backends import RemoteUserBackend
    from django.contrib.auth.views import login as django_login
    from django.contrib.auth.models import User
    from django.contrib.auth import REDIRECT_FIELD_NAME, authenticate, login
    from django.http import HttpResponseRedirect
    from django.core.exceptions import ObjectDoesNotExist
    import mit
    importedLdap = True
except ImportError, exp:
    importedLdap = False

@login_required(login_url=reverse_lazy('polls_login'))
def index(request, **kwargs):
    kerb = str(request.user)
    latest_poll_list = Poll.objects.all()
    answers_so_far = AnswerSet.objects.all().filter(active=True)
    for poll in latest_poll_list:
        try:
            answer_to_poll = answers_so_far.get(question=poll.id, name=kerb, active=True)
            poll.answer = answer_to_poll
        except (AnswerSet.DoesNotExist):
            poll.answer = None
    return render_to_response('polls/index.html', {'latest_poll_list': latest_poll_list, 'kerb': kerb})

def login(request):
    if 'kerberos' in request.GET and 'key' in request.GET:
        kerb = request.GET['kerberos']
        pw = request.GET['key']
        user = authenticate(username=kerb, password=pw)
        if user is not None:
            if user.is_active:
                return django_login(request, user, template_name='polls/login_fail.html')
            else:
                return HttpResponse('Your account has been disabled. Contact simmons-nominations@mit.edu for help.')
        else:
            return HttpResponse('kerb: ' + kerb + ', pw: ' + pw)
            return HttpResponse('Invalid login. Stop trying to mess around. Your actions are being logged.')
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
    if kerb[-8:].lower() == "@mit.edu":
        kerb = kerb[:-8]
    if Resident.objects.filter(athena=kerb).count() == 0:
        return render_to_response('polls/login_fail.html', {'email_error': kerb + ' is not a Simmons resident email! If you think it is, email simmons-nominations@mit.edu.'}, context_instance=RequestContext(request))
    password = random_string(20)
    user, created = User.objects.get_or_create(username=kerb)
    user.set_password(password)
    user.save()
    send_mail('Simmons Elections login info', 'Log in through this link: http://simmons-hall.scripts.mit.edu/elections/polls/login?kerberos=' + kerb + "&key=" + password, 
    'simmons-nominations@mit.edu', ['allenpark@mit.edu'], fail_silently=False)
    return HttpResponse('Please check your email for futher instructions.')
    
def random_string(length):
    return ''.join(random.choice(string.ascii_letters + string.digits) for x in xrange(length))

###
# Responses for various form displays

def form_choice_response(request, poll, kerb, answer, next_choice_num):
    logger.debug(kerb + " - Displaying form - " + poll.question + " - choice " + str(next_choice_num))
    return render_to_response('polls/detail.html', {
        'poll': poll,
        'answer': answer,
        'choice_num': next_choice_num,
        'kerb': kerb}, context_instance=RequestContext(request))

def form_error_response(request, poll, kerb, answer, error_message, next_choice_num = 1):
    return render_to_response('polls/detail.html', {
        'poll': poll,
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
    poll = get_object_or_404(Poll, pk=poll_id)

    #####
    # Get or create the answer set
    # Allows the form to display the user's previous responses
    (answer, answer_created) = AnswerSet.objects.get_or_create(name=kerb, question=poll, active=True)

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
        answer = AnswerSet(name=kerb, question=poll, active=True)

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
        (answer, answer_created) = AnswerSet.objects.get_or_create(name=kerb, question=poll, active=True)
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
