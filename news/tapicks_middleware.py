from django.http import HttpResponse, HttpResponseRedirect
import exceptions
from django.views.generic.simple import direct_to_template
from helpers import *
import models

class ExceptionHandlerMiddleware:
    
    def process_exception(self, request, exptn):
        if exptn.__class__ == exceptions.PrivateTopicNoAccess:
            return render(request, {'message':'You tried to access a topic which is private, and you are not a mamber.'}, 'news/no_prevs.html')
        elif exptn.__class__ == models.CanNotVote:
            return render(request, {'message':'You tried to vote or submit to a topic to which you are not subscribed, and the topic is memebers only.'}, 'news/no_prevs.html')