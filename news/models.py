from django.db import models
from django.contrib.auth.models import User
import defaults

class UserProfile(models.Model):
    user = models.ForeignKey(User)
    karma = models.IntegerField(default = 1)
    def __unicode__(self):
        return u'%s: %s' % (self.user, self.karma)

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

class TopicManager(models.Manager):
    "Manager for topics"
    def create_new_topic(self, user, full_name, topic_name, karma_factor = True):
        profile = user.get_profile()
        if profile.karma > defaults.KARMA_COST_NEW_TOPIC or not karma_factor:
            if karma_factor:
                profile.karma -= defaults.KARMA_COST_NEW_TOPIC
                profile.save()
            topic = Topic(name = topic_name, full_name = full_name, created_by = user)
            topic.save()
            return topic
        else:
            raise TooLittleKarmaForNewTopic
        
class Topic(models.Model):
    """A specific topic in the website."""
    name = models.CharField(max_length = 100, unique = True)
    full_name = models.TextField()
    created_by = models.ForeignKey(User)
    objects = TopicManager()
    
    def __unicode__(self):
        return u'%s' % self.name
    
class LinkManager(models.Manager):
    "Manager for links"
    def create_link(self, url, text, user, topic):
        profile = user.get_profile()
        if profile.karma > defaults.KARMA_COST_NEW_LINK:
            profile.karma -= defaults.KARMA_COST_NEW_LINK
            profile.save()
            link = Link(user = user, text = text, topic = topic, url=url)
            link.save()
            return link
        else:
            raise TooLittleKarmaForNewLink
        
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
    points = models.IntegerField(default = 0)
    
    def upvote(self, user):
        self.vote(user, True)
    
    def downvote(self, user):
        self.vote(user, False)
    
    def vote(self, user, direction = True):
        "Vote the given link either up or down, using a user. Calling multiple times with same user must have now effect."
        vote, created, flipped = LinkVote.objects.do_vote(user = user, link = self, direction = direction)
        save_vote = False
        if created and direction:
            self.liked_by_count += 1
            self.points += 1
            save_vote = True
            
        if created and not direction:
            self.disliked_by_count += 1
            self.points -= 1
            save_vote = True
         
        if direction and flipped:
            #Upvoted and Earlier downvoted
            self.liked_by_count += 1
            self.disliked_by_count -= 1
            save_vote = True
            
        if not direction and flipped:
            #downvoted and Earlier upvoted
            self.liked_by_count -= 1
            self.disliked_by_count += 1
            save_vote = True
        
        if save_vote:
            self.save()
            
    def reset_vote(self, user):
        "Reset a previously made vote"
        import pdb
        #pdb.set_trace()
        try:
            vote = LinkVote.objects.get(link = self, user = user)
        except LinkVote.DoesNotExist, e:
            "trying to reset vote, which does not exist."
            return
        if vote.direction:
            self.liked_by_count -= 1
            self.save()
        if not vote.direction:
            self.disliked_by_count -= 1
            self.save()
        vote.delete()
        
    
    objects = LinkManager()
    
    def __unicode__(self):
        return u'%s' % self.url
    
    class Meta:
        unique_together = ('url', 'topic')
        
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
        
        
class CommentManager(models.Manager):
    def create_comment(self, link, user, comment_text):
        comment = Comment(link = link, user = user, comment_text = comment_text)
        comment.save()
        return comment

class Comment(models.Model):
    "Comment on a link"
    link = models.ForeignKey(Link)
    user = models.ForeignKey(User)
    comment_text = models.TextField()
    created_on = models.DateTimeField(auto_now_add = 1)
    points = models.IntegerField(default = 0)
    
    objects = CommentManager()
    
    def upvote(self, user):
        self.vote(user, True)
        
    def downvote(self, user):
        self.vote(user, False)
    
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
    
    class Meta:
        unique_together = ('comment', 'user')

VALID_GROUPS = (('Owner', 'Owner'), ('Participant', 'Participant'), ('Viewer', 'Viewer'))
VALID_GROUPS_ = [grp[1] for grp in VALID_GROUPS]

class SubscribedUserManager(models.Manager):
    "Manager for SubscribedUser"
    def subscribe_user(self, user, topic, group):
        if not group in VALID_GROUPS_:
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
    
    def __unicode__(self):
        return u'%s : %s-%s' % (self.topic, self.user, self.group)
    
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
        
    
class LinkTag(models.Model):
    tag = models.ForeignKey(Tag)
    link = models.ForeignKey(Link)
    count = models.IntegerField(default = 1)
    
    objects = LinkTagManager()
    
    def __unicode__(self):
        return u'%s - %s' % (self.link, self.tag)
    
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
    
    class Meta:
        unique_together = ('link_tag', 'user')
    

    