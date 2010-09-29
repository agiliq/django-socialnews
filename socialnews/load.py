from django.core.management import setup_environ
import settings

setup_environ(settings)

from news import models, tests

class B:
    pass
import random

run_name = ''.join([random.choice('abcdefghijklmnop') for i in xrange(10)])

b= B()

user = models.User.objects.create_user(username="load%s"%run_name, email="demo@demo.com", password="demo")
user.save()
b.user = user
profile = models.UserProfile(user = user, karma = 10000)
profile.save()
topic = models.Topic.objects.create_new_topic(user = b.user, topic_name = 'cpp%s'%run_name, full_name='CPP primer')
b.topic = topic
        

num_user = 1000
num_links = 3000
num_votes = 100
#Create 10 users
users = []
for i in xrange(num_user):
    user = models.UserProfile.objects.create_user(user_name='%s%s'%(run_name, i), email='demo@demo.com', password='demo')
    users.append(user)

profile = b.user.get_profile()
profile.karma = 10000
profile.save()
b.user = models.User.objects.get(id = b.user.id)
links = []    
for i in xrange(num_links):
    link = models.Link.objects.create_link(user = b.user, topic = b.topic, url='http://%s%s.com'% (run_name, i), text=str(i) )
    links.append(link)
    
for user in users:
    votes = random.randint(2, num_votes)
    for i in xrange(votes):
        link = random.choice(links)
        print i, link, user
        link.upvote(user)
    

    



