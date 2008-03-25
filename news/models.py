from django.db import models
from django.contrib.auth.models import User
import defaults
from django.core.urlresolvers import reverse
from urllib2 import urlparse
from datetime import datetime

class UserProfileManager(models.Manager):
    def create_user(self, user_name, email, password):
        "Create user and associate a profile with it."
        user = User.objects.create_user(user_name, email, password)
        profile = UserProfile(user = user)
        profile.save()
        return user
    
class UserProfile(models.Model):
    user = models.ForeignKey(User, unique = True)
    karma = models.IntegerField(default = defaults.DEFAULT_PROFILE_KARMA)
    
    objects = UserProfileManager()
    
    def __unicode__(self):
        return u'%s: %s' % (self.user, self.karma)
    
    class Admin:
        pass

class TooLittleKarma(Exception):
    "Exception signifying too little karma for the action."
    pass

class TooLittleKarmaForNewTopic(TooLittleKarma):
    "too little karma to create a topic."
    pass

class TooLittleKarmaForNewLink(TooLittleKarma):
    "too little karma to add a link."
    pass

class InvalidGroup(Exception):
    pass

class CanNotUnsubscribe(Exception):
    "Can not unsubscribe out"
    pass

topic_permissions = (('Public', 'Public'), ('Member', 'Member'), ('Private', 'Private'))
topic_permissions_flat = [perm[0] for perm in topic_permissions]

class TopicManager(models.Manager):
    "Manager for topics"
    def create_new_topic(self, user, full_name, topic_name, permissions = topic_permissions_flat[0], about=None, karma_factor = True):
        "Create topic and subscribe user to the given topic."
        profile = user.get_profile()
        if profile.karma > defaults.KARMA_COST_NEW_TOPIC or not karma_factor:
            if not about:
                about = 'About %s' % topic_name
            if karma_factor:
                profile.karma -= defaults.KARMA_COST_NEW_TOPIC
                profile.save()
            topic = Topic(name = topic_name, full_name = full_name, created_by = user, permissions = permissions, about = about)
            topic.save()
            subs_user = SubscribedUser.objects.subscribe_user(user = user, topic = topic, group = 'Moderator')
            return topic
        else:
            raise TooLittleKarmaForNewTopic
        
class Topic(models.Model):
    """A specific topic in the website."""
    name = models.CharField(max_length = 100, unique = True)
    full_name = models.TextField()
    created_by = models.ForeignKey(User)
    created_on = models.DateTimeField(auto_now_add = 1)
    updated_on = models.DateTimeField(auto_now = 1)
    num_links = models.IntegerField(default = 0)
    permissions = models.CharField(max_length = 100, choices = topic_permissions, default = topic_permissions_flat[0])
    about = models.TextField(default = '')
    
    objects = TopicManager()
    
    def __unicode__(self):
        return u'%s' % self.name
    
    class Admin:
        pass
    
    def get_absolute_url(self):
        return reverse('topic', kwargs={'topic_name':self.name})
    
    def subscribe_url(self):
        url = reverse('subscribe', kwargs={'topic_name':self.name})
        return url
    
    def unsubscribe_url(self):
        url = reverse('unsubscribe', kwargs={'topic_name':self.name})
        return url
    
    def submit_url(self):
        url = reverse('link_submit', kwargs={'topic_name':self.name})
        return url
    
    def manage_url(self):
        url = reverse('manage_topic', kwargs={'topic_name':self.name})
    
    
class LinkManager(models.Manager):
    "Manager for links"
    def create_link(self, url, text, user, topic, karma_factor=True):
        profile = user.get_profile()
        if profile.karma > defaults.KARMA_COST_NEW_LINK or not karma_factor:            
            profile.karma -= defaults.KARMA_COST_NEW_LINK
            profile.save()
            link = Link(user = user, text = text, topic = topic, url=url)
            link.points = user.get_profile().karma
            link.save()
            link.upvote(user)
            link.topic.num_links += 1
            link.topic.save()
            count = Link.objects.count()
            if not count % defaults.DAMPEN_POINTS_AFTER:
                Link.objects.dampen_points(link.topic)
            return link
        else:
            raise TooLittleKarmaForNewLink
        
    def get_query_set(self):
        return super(LinkManager, self).get_query_set().extra(select = {'comment_count':'SELECT count(news_comment.id) FROM news_comment WHERE news_comment.link_id = news_link.id', 'visible_points':'news_link.liked_by_count - news_link.disliked_by_count'})
    
    def get_query_set_with_user(self, user):
        qs = self.get_query_set().extra({'liked':'SELECT news_linkvote.direction FROM news_linkvote WHERE news_linkvote.link_id = news_link.id AND news_linkvote.user_id = %s' % user.id, 'disliked':'SELECT not news_linkvote.direction FROM news_linkvote WHERE news_linkvote.link_id = news_link.id AND news_linkvote.user_id = %s' % user.id, 'saved':'SELECT 1 FROM news_savedlink WHERE news_savedlink.link_id = news_link.id AND news_savedlink.user_id=%s'%user.id})
        return qs
    
    def dampen_points(self, topic):
        from django.db import connection
        cursor = connection.cursor()
        stmt = 'UPDATE news_link SET points = points/%s WHERE topic_id = %s AND points > 1' % (defaults.DAMP_FACTOR, topic.id)
        cursor.execute(stmt)
        
        
    def up_vote(self, user, link):
        pass
    
    
class Link(models.Model):
    "A specific link within a topic."
    url = models.URLField()
    text = models.TextField()
    user = models.ForeignKey(User, related_name="added_links")
    topic = models.ForeignKey(Topic)
    created_on = models.DateTimeField(auto_now_add = 1)
    liked_by = models.ManyToManyField(User, related_name="liked_links")
    disliked_by = models.ManyToManyField(User, related_name="disliked_links")
    liked_by_count = models.IntegerField(default = 0)
    disliked_by_count = models.IntegerField(default = 0)
    points = models.DecimalField(default = 0, max_digits=7, decimal_places=2)
    
    objects = LinkManager()
    
    """The Voting algo:
    On each upvote increase the points by min(voter.karma, 10)
    On each upvote decrease the points by min(voter.karma, 10)
    increase/decrease the voters karma by 1
    """
    
    def upvote(self, user):
        return self.vote(user, True)
    
    def downvote(self, user):
        return self.vote(user, False)
    
    def vote(self, user, direction = True):
        "Vote the given link either up or down, using a user. Calling multiple times with same user must have now effect."
        vote, created, flipped = LinkVote.objects.do_vote(user = user, link = self, direction = direction)
        save_vote = False
        change = max(0, min(defaults.MAX_CHANGE_PER_VOTE, user.get_profile().karma))
        if created and direction:
            self.liked_by_count += 1
            self.points += change
            save_vote = True
            profile = self.user.get_profile()
            profile.karma += defaults.CREATORS_KARMA_PER_VOTE
            profile.save()
            
        if created and not direction:
            self.disliked_by_count += 1
            self.points -= change
            save_vote = True
            profile = self.user.get_profile()
            profile.karma -= defaults.CREATORS_KARMA_PER_VOTE
            profile.save()
         
        if direction and flipped:
            #Upvoted and Earlier downvoted
            self.liked_by_count += 1
            self.disliked_by_count -= 1
            self.points += 2*change
            save_vote = True
            profile = self.user.get_profile()
            profile.karma += 2 * defaults.CREATORS_KARMA_PER_VOTE
            profile.save()
            
        if not direction and flipped:
            #downvoted and Earlier upvoted
            self.liked_by_count -= 1
            self.disliked_by_count += 1
            self.points -= 2*change
            save_vote = True
            profile = self.user.get_profile()
            profile.karma -= 2 * defaults.CREATORS_KARMA_PER_VOTE
            profile.save()
        
        if save_vote:
            self.save()
        return vote
            
    def reset_vote(self, user):
        "Reset a previously made vote"
        try:
            vote = LinkVote.objects.get(link = self, user = user)
        except LinkVote.DoesNotExist, e:
            "trying to reset vote, which does not exist."
            return
        if vote.direction:
            self.liked_by_count -= 1
            self.save()
            profile = self.user.get_profile()
            profile.karma -= defaults.CREATORS_KARMA_PER_VOTE
            profile.save()
        if not vote.direction:
            self.disliked_by_count -= 1
            self.save()
            profile = self.user.get_profile()
            profile.karma += defaults.CREATORS_KARMA_PER_VOTE
            profile.save()
        vote.delete()
        return vote
        
    def site(self):
        "Return the site where this link was posted."
        return urlparse.urlparse(self.url)[1]
    
    def vis_points(self):
        vis_points = self.liked_by_count - self.disliked_by_count
        return vis_points
    
    def humanized_time(self):
        return humanized_time(self.created_on)
    
    
        
    def get_absolute_url(self):
        url = reverse('link_detail', kwargs = dict(topic_name = self.topic.name, link_id = self.id))
        return url
    
    def save_url(self):
        url = reverse('save_link', kwargs = dict(topic_name = self.topic.name, link_id = self.id))
        return url
    
    def __unicode__(self):
        return u'%s' % self.url
    
    class Admin:
        pass
    
    class Meta:
        unique_together = ('url', 'topic')
        ordering = ('points', '-created_on')
        
class SavedLinkManager(models.Manager):
    def save_link(self, link, user):
        try:
            return SavedLink.objects.get(link = link, user = user)
        except SavedLink.DoesNotExist:
            pass            
        savedl = SavedLink(link = link, user = user)
        savedl.save()
        return savedl
    
        
class SavedLink(models.Model):
    link = models.ForeignKey(Link)
    user = models.ForeignKey(User)
    created_on = models.DateTimeField(auto_now_add = 1)
    
    objects = SavedLinkManager()
    
    class Admin:
        pass
    
    class Meta:
        unique_together = ('link', 'user')
        ordering = ('-created_on', )
        
class VoteManager(models.Manager):
    "Handle voting for LinkVotes, Commentvotes"
    def do_vote(self, user, object, direction, voted_class,):
        "Vote a link by an user. Create if vote does not exist, or change direction if needed."
        if voted_class == LinkVote:
            vote, created = voted_class.objects.get_or_create(user = user, link = object)
        elif  voted_class == CommentVote:
            vote, created = voted_class.objects.get_or_create(user = user, comment = object)
        flipped = False
        if not direction == vote.direction:    
            vote.direction = direction
            vote.save()
            if not created:
                flipped = True
        return vote, created, flipped
        
class LinkVoteManager(VoteManager):
    "Manager for linkvotes"
    """def do_vote(self, user, link, direction):
        "Vote a link by an user. Create if vote does not exist, or change direction if needed."
        vote, created = LinkVote.objects.get_or_create(user = user, link = link)
        flipped = False
        if not direction == vote.direction:    
            vote.direction = direction
            vote.save()
            if not created:
                flipped = True
        return vote, created, flipped"""
    def do_vote(self, user, link, direction):
        return super(LinkVoteManager, self).do_vote(user = user, object = link, direction = direction, voted_class = LinkVote, )
        
        
        
class LinkVote(models.Model):
    "Vote on a specific link"
    link = models.ForeignKey(Link)
    user = models.ForeignKey(User)
    direction = models.BooleanField()#Up is true, down is false.
    created_on = models.DateTimeField(auto_now_add = 1)
    
    objects = LinkVoteManager()
    
    def __unicode__(self):
        return u'%s: %s - %s' % (self.link, self.user, self.direction)
    
    class Meta:
        unique_together = ('link', 'user')
        
    class Admin:
        pass
        
        
class CommentManager(models.Manager):
    def get_query_set_with_user(self, user):
        #qs = self.get_query_set().extra({'liked':'SELECT news_commentvote.direction FROM news_commentvote WHERE news_commentvote.comment_id = news_comment.id AND news_commentvote.user_id = %s' % user.id, 'disliked':'SELECT not news_commentvote.direction FROM news_commentvote WHERE news_commentvote.comment_id = news_comment.id AND news_commentvote.user_id = %s' % user.id})
        qs = self.append_user_data(self.get_query_set(), user)
        return qs
    
    def append_user_data(self, queryset, user):
        return queryset.extra({'liked':'SELECT news_commentvote.direction FROM news_commentvote WHERE news_commentvote.comment_id = news_comment.id AND news_commentvote.user_id = %s' % user.id, 'disliked':'SELECT not news_commentvote.direction FROM news_commentvote WHERE news_commentvote.comment_id = news_comment.id AND news_commentvote.user_id = %s' % user.id})
        

    
    def create_comment(self, link, user, comment_text, parent = None):
        comment = Comment(link = link, user = user, comment_text = comment_text, parent = parent)
        comment.save()
        comment.upvote(user)
        return comment

class Comment(models.Model):
    "Comment on a link"
    link = models.ForeignKey(Link)
    user = models.ForeignKey(User)
    comment_text = models.TextField()
    created_on = models.DateTimeField(auto_now_add = 1)
    points = models.IntegerField(default = 0)
    parent = models.ForeignKey('Comment', null=True, blank=True, related_name='children')
    
    objects = CommentManager()
    
    def get_subcomment_form(self):
        from bforms import DoThreadedComment
        form = DoThreadedComment(user = self.user, link = self.link, parent=self)
        return form
    
    def __str__(self):
        return u'%s' % (self.comment_text)
    
    def upvote(self, user):
        return self.vote(user, True)
        
    def downvote(self, user):
        return self.vote(user, False)
    
    def vote(self, user, direction):
        vote, created, flipped = CommentVote.objects.do_vote(self, user, direction)
        if created and direction:
            self.points += 1
        elif created and not direction:
            self.points -= 1
        elif flipped and direction:
            #Earlier downvote, now upvote
            self.points += 2
        elif flipped and not direction:
            #Earlier upvote, now downvote
            self.points -= 2
        self.save()
        return vote
        
    def reset_vote(self, user):
        try:
            vote = CommentVote.objects.get(comment = self, user = user)
        except CommentVote.DoesNotExist:
            #Cant reset un unexisting vote, return
            return
        if vote.direction:
            #reset existing upvote
            self.points -= 1
            self.save()
        elif not vote.direction:
            self.points += 1
            self.save()
        vote.delete()
        return vote
        
    def humanized_time(self):
        return humanized_time(self.created_on)
    
    def downvote_url(self):
        return reverse('downvote_comment', kwargs={'comment_id':self.id})
    
    
    def upvote_url(self):
        return reverse('upvote_comment', kwargs={'comment_id':self.id})
    
    class Meta:
        ordering = ('-created_on', )
        
import mptt
mptt.register(Comment)
            
class CommentVotesManager(VoteManager):
    def do_vote(self, comment, user, direction):
        return super(CommentVotesManager, self).do_vote(user = user, object = comment, direction = direction, voted_class = CommentVote, )    
    
class CommentVote(models.Model):
    "Votes on a comment"
    comment = models.ForeignKey(Comment)
    user = models.ForeignKey(User)
    direction = models.BooleanField()#Up is true, down is false.
    created_on = models.DateTimeField(auto_now_add = 1)
    
    objects = CommentVotesManager()
    
    class Admin:
        pass
    
    class Meta:
        unique_together = ('comment', 'user')

VALID_GROUPS = (('Moderator', 'Moderator'), ('Member', 'Member'))
VALID_GROUPS_FLAT = [grp[1] for grp in VALID_GROUPS]

class SubscribedUserManager(models.Manager):
    "Manager for SubscribedUser"
    def subscribe_user(self, user, topic, group):
        if not group in VALID_GROUPS_FLAT:
            raise InvalidGroup('%s is not a valid group' % group)
        subs = SubscribedUser(user = user, topic = topic, group = group)
        subs.save()
        return subs
    
    
class SubscribedUser(models.Model):
    "Users who are subscribed to a Topic"
    topic = models.ForeignKey(Topic)
    user = models.ForeignKey(User)
    group = models.CharField(max_length = 10)
    subscribed_on = models.DateTimeField(auto_now_add = 1)
    
    objects = SubscribedUserManager()
    
    def delete(self):
        "If user created the topic, they can not be unssubscribed"
        if self.topic.created_by == self.user:
            raise CanNotUnsubscribe
        super(SubscribedUser, self).delete()
        
    def is_creator(self):
        "Is the subscriber creator of the topic"
        return self.topic.created_by == self.user
    
    def is_moderator(self):
        if self.group == 'Moderator':
            return True
        return False
    
    def set_group(self, group):
        if not group in VALID_GROUPS_FLAT:
            raise InvalidGroup('%s is not a valid group' % group)
        self.group = group
        self.save()
    
    def __unicode__(self):
        return u'%s : %s-%s' % (self.topic, self.user, self.group)
    
    class Admin:
        pass
    
    class Meta:
        unique_together = ('topic', 'user')
        
class TagManager(models.Manager):
    def create_tag(self, tag_text, topic):
        "Create a sitwide tag if needed, and a per topic tag if needed. Return them as sitewide_tag, followed by topic_tag"
        try:
            sitewide_tag = Tag.objects.get(text = tag_text, topic__isnull = True)
        except Tag.DoesNotExist:
            sitewide_tag = Tag(text = tag_text, topic = None)
            sitewide_tag.save()
        
        topic_tag, created = Tag.objects.get_or_create(text = tag_text, topic = topic)
        
        return sitewide_tag, topic_tag
        
class Tag(models.Model):
    """Links can be tagged as.
    There are two types of tags. If topic is not none this is a per topic tag.
    Else this is a sitewide tag. So when a link is first tagged, two tags get created."""
    text = models.CharField(max_length = 100)
    topic = models.ForeignKey(Topic, null = True)
    
    objects = TagManager()
    
    def get_absolute_url(self):
        if self.topic:
            return reverse('topic_tag', kwargs = {'topic_name':self.topic.name, 'tag_text':self.text})
        else:
            return reverse('sitewide_tag', kwargs = {'tag_text':self.text})
    class Admin:
        pass
    
    class Meta:
        unique_together = ('text', 'topic')
    
class LinkTagManager(models.Manager):
    def tag_link(self, link, tag_text):
        "Tag a page"
        site_tag, topic_tag  = Tag.objects.create_tag(tag_text = tag_text, topic = link.topic)
        topic_link_tag, created = LinkTag.objects.get_or_create(tag = topic_tag, link = link)
        topic_link_tag.save()
        site_link_tag, created = LinkTag.objects.get_or_create(tag = site_tag, link = link)
        site_link_tag.save()
        return site_link_tag, topic_link_tag
    
    def get_topic_tags(self):
        return self.filter(tag__topic__isnull = False).select_related()
    
    def get_sitewide_tags(self):
        return self.filter(tag__topic__isnull = True).select_related()
        
    
class LinkTag(models.Model):
    tag = models.ForeignKey(Tag)
    link = models.ForeignKey(Link)
    count = models.IntegerField(default = 1)
    
    objects = LinkTagManager()
    
    def __unicode__(self):
        return u'%s - %s' % (self.link, self.tag)
    
    class Admin:
        pass
    
    class Meta:
        unique_together = ('tag', 'link')
        
class LinkTagUserManager(models.Manager):
    def tag_link(self, tag_text, link, user):
        site_link_tag, topic_link_tag = LinkTag.objects.tag_link(tag_text = tag_text, link = link)
        user_tag = LinkTagUser.objects.get_or_create(link_tag = topic_link_tag, user = user)
        return user_tag   
        
class LinkTagUser(models.Model):
    link_tag  = models.ForeignKey(LinkTag)
    user = models.ForeignKey(User)
    
    objects = LinkTagUserManager()
    
    class Admin:
        pass
    
    class Meta:
        unique_together = ('link_tag', 'user')
        
def humanized_time(time):
        "Time in human friendly way, like, 1 hrs ago, etc"
        now = datetime.now()
        delta = now - time
        "try if days have passed."
        if delta.days:
            if delta.days == 1:
                return 'yesterday'
            else:
                return time.strftime(defaults.DATE_FORMAT)
        delta = delta.seconds
        if delta < 60:
            return '%s seconds ago' % delta
        elif delta < 60 * 60:
            return '%s minutes ago' % (delta/60)
        elif delta < 60 * 60 * 24:
            return '%s hours ago' % (delta/(60 * 60))        
    

    