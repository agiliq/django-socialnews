
import urllib2

try:
    import simplejson
except ImportError:
    from django.utils import simplejson

from django.core.management.base import NoArgsCommand, CommandError
from django.conf import settings
from django.contrib.auth.models import User

from news.models import Link, Topic

class Command(NoArgsCommand):
    help = 'Update the site with links from a API, expects the response in JSON format'
    
    def handle_noargs(self, **options):
        if not hasattr(settings, 'JSON_API_URL'):
            raise CommandError('Required parameter JSON_API_URL not defined in settings.')
        
        username = getattr(settings, 'API_ADMIN_USER', None)
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                raise CommandError('User with name "%s", specified as settings.API_ADMIN_USER, not found.' % (username))    
        else:
            super_users = User.objects.filter(is_superuser=True)
            if super_users.count():
                user = super_users[0]
            else:
                raise CommandError('No admin user found.')
        
        if not username and user:
            user_decision = raw_input('''API_ADMIN_USER is not defined in the settings, using "%s" to get the data from API \nIf you want to use a differnt user specify in the settings.API_ADMIN_USER.\nContinue using "%s" (yes/no): ''' %(user.username, user.username))
            if user_decision.lower() == 'no':
                raise CommandError('Aborting because you said so.')
        
        import ipdb
        ipdb.set_trace()
        profile = user.get_profile()
        topic = profile.default_topic
        
        api_data = urllib2.urlopen(settings.JSON_API_URL).read()
        
        KEYS_MAPPING = {'title': 'title', 'description': 'description', 'url': 'url'}
        api_data = open('tmp/sample_json.txt').read()
        KEYS_MAPPING = {'title': 'title', 'description': 'text', 'url': 'story_link'}

        """
        call any custom JSON serizliser/deserializer here 
        as the code assumes the 
        1. title
        2. text
        3. story_link 
        keys in the links of the JSON object
        
        or update the KEYS_MAPPING dictionary with the correponding attribute names.
        
        EX: if 'text' is the name of key for 'description' & 
               'story_link' is the name of key for 'url' then
            KEYS_MAPPING = {'title': 'title', 'description': 'text', 'url': 'story_link'}
        """
        
        json_data = simplejson.loads(api_data)
        for link in json_data:
            title = link[KEYS_MAPPING['title']]
            description = link[KEYS_MAPPING['description']]
            url = link[KEYS_MAPPING['url']]
            Link.objects.create_link(url=url, 
                                     text=description, 
                                     user=user, 
                                     topic=topic, 
                                     summary=title,)
