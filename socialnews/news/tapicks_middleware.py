
from news import exceptions
from news.helpers import *

class ExceptionHandlerMiddleware:
    
    def process_exception(self, request, exptn):
        from news import models
        message = None
        if exptn.__class__ == exceptions.PrivateTopicNoAccess:
            message = 'You tried to access a topic which is private, and you are not a mamber.'
        elif exptn.__class__ == models.CanNotVote:
            message = 'You tried to vote or submit to a topic to which you are not subscribed, and the topic is memebers only.'
        
        if not message:
            return 
        return render(request, {'message': message}, 'news/no_prevs.html')