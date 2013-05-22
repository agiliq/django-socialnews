
import random
from urllib2 import urlparse
from datetime import datetime

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models

from autoslug import AutoSlugField
from news import defaults

class SiteSetting(models.Model):
    default_topic = models.ForeignKey('Topic')


class UserProfileManager(models.Manager):
    def create_user(self, user_name, email, password):
        "Create user and associate a profile with it."
        user = User.objects.create_user(user_name, email, password)
        profile = UserProfile(user = user)
        chars = 'abcdefghijklmnopqrstuvwxyz'
        profile.secret_key = ''.join([random.choice(chars) for i in xrange(20)])
        settings = SiteSetting.objects.all()[0]#There can be only one SiteSettings
        SubscribedUser.objects.subscribe_user(user = user, topic = settings.default_topic)
        profile.default_topic = settings.default_topic
        profile.save()
        return user


class UserProfile(models.Model):
    user = models.ForeignKey(User, unique = True)
    email_validated = models.BooleanField(default = False)
    karma = models.IntegerField(default = defaults.DEFAULT_PROFILE_KARMA)
    recommended_calc = models.DateTimeField(auto_now_add = 1)#when was the recommended links calculated?
    is_recommended_calc = models.BooleanField(default = False)
    default_topic = models.ForeignKey('Topic', blank = True, null = True)
    secret_key = models.CharField(max_length = 50)

    objects = UserProfileManager()

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


class CanNotUnsubscribe(Exception):
    "Can not unsubscribe out"
    pass


class CanNotVote(Exception):
    "Can not vote. Not a member."
    pass


topic_permissions = (('Public', 'Public'), ('Member', 'Member'), ('Private', 'Private'))
topic_permissions_flat = [perm[0] for perm in topic_permissions]

class TopicManager(models.Manager):
    "Manager for topics"
    def create_new_topic(self, user, full_name, topic_name, permissions = topic_permissions_flat[0], about=None, karma_factor = True):
        "Create topic and subscribe user to the given topic."
        profile = user.get_profile()
        if profile.karma >= defaults.KARMA_COST_NEW_TOPIC or not karma_factor:
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

    def all(self):
        return super(TopicManager, self).all().exclude(permissions='Private')

    def real_all(self):
        return super(TopicManager, self).all()

    def append_user_data(self, user):
        return self.get_query_set().extra({'is_subscribed':'SELECT 1 FROM news_subscribeduser WHERE topic_id = news_topic.id AND user_id = %s' % user.id})


class Topic(models.Model):
    """A specific topic in the website."""
    name = models.CharField(max_length=100, unique=True)
    slug = AutoSlugField(populate_from='name', unique=True, max_length=100)
    full_name = models.TextField()
    created_by = models.ForeignKey(User)
    created_on = models.DateTimeField(auto_now_add = 1)
    updated_on = models.DateTimeField(auto_now = 1)
    num_links = models.IntegerField(default=0)
    permissions = models.CharField(max_length = 100, choices = topic_permissions, default = topic_permissions_flat[0])
    about = models.TextField(default = '')

    objects = TopicManager()

    def __unicode__(self):
        return u'%s' % self.name

    def get_absolute_url(self):
        return reverse('topic', kwargs={'topic_slug': self.slug})

    def subscribe_url(self):
        url = reverse('subscribe', kwargs={'topic_slug': self.slug})
        return url

    def unsubscribe_url(self):
        url = reverse('unsubscribe', kwargs={'topic_slug': self.slug})
        return url

    def submit_url(self):
        url = reverse('link_submit', kwargs={'topic_slug': self.slug})
        return url

    def about_url(self):
        return reverse('topic_about', kwargs={'topic_slug': self.slug})

    def new_url(self):
        return reverse('topic_new', kwargs={'topic_slug': self.slug})

    def manage_url(self):
        url = reverse('topic_manage', kwargs={'topic_name':self.name})
        return url


class InviteManager(models.Manager):
    def invite_user(self, user, topic, text=None):
        invite= Invite(user = user, topic = topic, invite_text = text)
        invite.save()
        return invite


class Invite(models.Model):
    user = models.ForeignKey(User)
    topic = models.ForeignKey(Topic)
    invite_text = models.TextField(null = True, blank = True)

    objects = InviteManager()

    class Meta:
        unique_together = ('user', 'topic')


class LinkManager(models.Manager):
    "Manager for links"
    def create_link(self, url, text, user, topic, summary, karma_factor=True):
        profile = user.get_profile()
        if profile.karma > defaults.KARMA_COST_NEW_LINK or not karma_factor:
            profile.karma -= defaults.KARMA_COST_NEW_LINK
            profile.save()
            link = Link(user=user, summary=summary, text=text, topic=topic, url=url)
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

    def all(self):
        return super(LinkManager, self).all().exclude(topic__permissions='Private')

    def real_all(self):
        return super(LinkManager, self).all()

    def get_query_set(self):
        return super(LinkManager, self).get_query_set().extra(select = {'comment_count':'SELECT count(news_comment.id) FROM news_comment WHERE news_comment.link_id = news_link.id', 'visible_points':'news_link.liked_by_count - news_link.disliked_by_count'},)

    def get_query_set_with_user(self, user):
        can_vote_sql = """
        SELECT 1 FROM news_topic
        WHERE news_link.topic_id = news_topic.id
        AND news_topic.permissions ='Public'
        UNION
        SELECT 1 from news_topic, news_subscribeduser
        WHERE news_link.topic_id = news_topic.id
        AND news_subscribeduser.topic_id = news_topic.id
        AND news_subscribeduser.user_id = %s
        AND NOT news_topic.permissions ='Public'
        """ % user.id
        qs = self.get_query_set().extra({'liked':'SELECT news_linkvote.direction FROM news_linkvote WHERE news_linkvote.link_id = news_link.id AND news_linkvote.user_id = %s' % user.id, 'disliked':'SELECT not news_linkvote.direction FROM news_linkvote WHERE news_linkvote.link_id = news_link.id AND news_linkvote.user_id = %s' % user.id, 'saved':'SELECT 1 FROM news_savedlink WHERE news_savedlink.link_id = news_link.id AND news_savedlink.user_id=%s'%user.id, 'can_vote':can_vote_sql}, tables=['news_topic',], where=['news_topic.id = news_link.topic_id', "(news_topic.permissions in ('%s', '%s') OR exists (SELECT 1 FROM news_subscribeduser WHERE news_subscribeduser.user_id = %s AND news_subscribeduser.topic_id = news_topic.id AND news_topic.permissions in ('%s')))"%('Public', 'Member', user.id, 'Private')], )
        return qs

    def dampen_points(self, topic):
        from django.db import connection
        cursor = connection.cursor()
        stmt = 'UPDATE news_link SET points = ROUNDints/%s, 0) WHERE topic_id = %s AND points > 1' % (defaults.DAMP_FACTOR, topic.id)
        cursor.execute(stmt)


class Link(models.Model):
    "A specific link within a topic."
    url = models.URLField()
    summary = models.CharField(max_length=255)
    slug = AutoSlugField(populate_from='summary', unique=True, max_length=255)
    text = models.TextField(u'Description')
    user = models.ForeignKey(User, related_name="added_links")
    topic = models.ForeignKey(Topic)
    created_on = models.DateTimeField(auto_now_add = 1)
    liked_by = models.ManyToManyField(User, related_name="liked_links")
    disliked_by = models.ManyToManyField(User, related_name="disliked_links")
    liked_by_count = models.IntegerField(default = 0)
    disliked_by_count = models.IntegerField(default = 0)
    points = models.DecimalField(default = 0, max_digits=7, decimal_places=2)
    recommended_done = models.BooleanField(default = False)
    #
    related_links_calculated = models.BooleanField(default = False)

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

        "Vote the given link either up or down, using a user. Calling multiple times with same user must have no effect."
        #Check if the current user can vote this, link or raise exception
        if self.topic.permissions == 'Public':
            pass #Anyone can vote
        else:
            try:
                subscribed_user = SubscribedUser.objects.get(topic = self.topic, user = user)
            except SubscribedUser.DoesNotExist:
                raise CanNotVote('The topic %s is non-public, and you are not subscribed to it.' % self.topic.name)
        vote, created, flipped = LinkVote.objects.do_vote(user = user, link = self, direction = direction)
        save_vote = False
        profile = user.get_profile()
        change = max(0, min(defaults.MAX_CHANGE_PER_VOTE, profile.karma))
        if created and direction:
            self.liked_by_count += 1
            self.points += change
            save_vote = True
            profile = self.user.get_profile()
            profile.karma += defaults.CREATORS_KARMA_PER_VOTE

        if created and not direction:
            self.disliked_by_count += 1
            self.points -= change
            save_vote = True
            profile = self.user.get_profile()
            profile.karma -= defaults.CREATORS_KARMA_PER_VOTE

        if direction and flipped:
            #Upvoted and Earlier downvoted
            self.liked_by_count += 1
            self.disliked_by_count -= 1
            self.points += 2*change
            save_vote = True
            profile = self.user.get_profile()
            profile.karma += 2 * defaults.CREATORS_KARMA_PER_VOTE

        if not direction and flipped:
            #downvoted and Earlier upvoted
            self.liked_by_count -= 1
            self.disliked_by_count += 1
            self.points -= 2*change
            save_vote = True
            profile = self.user.get_profile()
            profile.karma -= 2 * defaults.CREATORS_KARMA_PER_VOTE
        if not user == self.user:
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
        change = max(0, min(defaults.MAX_CHANGE_PER_VOTE, user.get_profile().karma))
        if vote.direction:
            self.liked_by_count -= 1
            self.points -= change
            self.save()
            profile = self.user.get_profile()
            profile.karma -= defaults.CREATORS_KARMA_PER_VOTE
        if not vote.direction:
            self.points += change
            self.disliked_by_count -= 1
            self.save()
            profile = self.user.get_profile()
            profile.karma += defaults.CREATORS_KARMA_PER_VOTE
        if not user == self.user:
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
        # url = reverse('link_detail', kwargs = dict(topic_name = self.topic.name, link_id = self.id))
        return reverse('link_detail', kwargs={'topic_slug': self.topic.slug, 'link_slug': self.slug})

    def save_url(self):
        url = reverse('save_link', kwargs={'link_id': self.id})
        return url

    def related_url(self):
        url = reverse('link_related', kwargs={'topic_slug': self.topic.slug, 'link_slug': self.slug})
        return url

    def info_url(self):
        url = reverse('link_info', kwargs={'topic_slug': self.topic.slug, 'link_slug': self.slug})
        return url

    def as_text(self):
        "Full textual represenatation of link"
        return '%s %s topic:%s user:%s' % (self.url, self.text, self.topic, self.user.username)

    def __unicode__(self):
        return u'%s' % self.url

    class Meta:
        unique_together = ('url', 'topic')
        ordering = ('-points', '-created_on')


class SavedLinkManager(models.Manager):
    def save_link(self, link, user):
        try:
            return SavedLink.objects.get(link = link, user = user)
        except SavedLink.DoesNotExist:
            pass
        savedl = SavedLink(link = link, user = user)
        savedl.save()
        return savedl

    def get_user_data(self):
        can_vote_sql = """
        SELECT 1 FROM news_topic, news_link
        WHERE news_link.topic_id = news_topic.id
        AND news_link.id = news_savedlink.link_id
        AND news_topic.permissions ='Public'
        UNION
        SELECT 1 from news_topic, news_subscribeduser, news_link
        WHERE news_link.topic_id = news_topic.id
        AND news_link.id = news_savedlink.link_id
        AND news_subscribeduser.topic_id = news_topic.id
        AND news_subscribeduser.user_id = news_savedlink.user_id
        AND NOT news_topic.permissions ='Public'
        """
        return self.get_query_set().extra({'liked':'SELECT direction FROM news_linkvote WHERE news_linkvote.link_id = news_savedlink.link_id AND news_linkvote.user_id = news_savedlink.user_id', 'disliked':'SELECT NOT direction FROM news_linkvote WHERE news_linkvote.link_id = news_savedlink.link_id AND news_linkvote.user_id = news_savedlink.user_id', 'saved':'SELECT 1', 'can_vote':can_vote_sql})


class SavedLink(models.Model):
    link = models.ForeignKey(Link)
    user = models.ForeignKey(User)
    created_on = models.DateTimeField(auto_now_add = 1)

    objects = SavedLinkManager()

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

    def get_user_data(self):
        can_vote_sql = """
        SELECT 1 FROM news_topic, news_link
        WHERE news_link.topic_id = news_topic.id
        AND news_link.id = news_linkvote.link_id
        AND news_topic.permissions ='Public'
        UNION
        SELECT 1 from news_topic, news_subscribeduser, news_link
        WHERE news_link.topic_id = news_topic.id
        AND news_link.id = news_linkvote.link_id
        AND news_subscribeduser.topic_id = news_topic.id
        AND news_subscribeduser.user_id = news_linkvote.user_id
        AND NOT news_topic.permissions ='Public'
        """
        return self.get_query_set().extra({'liked':'direction', 'disliked':'NOT direction', 'saved':'SELECT 1 FROM news_savedlink WHERE news_savedlink.link_id = news_linkvote.link_id AND news_savedlink.user_id = news_linkvote.user_id', 'can_vote':can_vote_sql})


class LinkVote(models.Model):
    "Vote on a specific link"
    link = models.ForeignKey(Link)
    user = models.ForeignKey(User)
    direction = models.BooleanField(default = True)#Up is true, down is false.
    created_on = models.DateTimeField(auto_now_add = 1)

    objects = LinkVoteManager()

    def __unicode__(self):
        return u'%s: %s - %s' % (self.link, self.user, self.direction)

    class Meta:
        unique_together = ('link', 'user')


class RelatedLinkManager(models.Manager):
    "Manager for related links."
    def get_query_set_with_user(self, user):
        liked_sql = 'SELECT news_linkvote.direction FROM news_linkvote WHERE news_linkvote.link_id = news_relatedlink.related_link_id AND news_linkvote.user_id = %s' % user.id
        can_vote_sql = """
        SELECT 1 FROM news_topic, news_link
        WHERE news_link.topic_id = news_topic.id
        AND news_link.id = news_relatedlink.related_link_id
        AND news_topic.permissions ='Public'
        UNION
        SELECT 1 from news_topic, news_subscribeduser, news_link
        WHERE news_link.topic_id = news_topic.id
        AND news_link.id = news_relatedlink.related_link_id
        AND news_subscribeduser.topic_id = news_topic.id
        AND news_subscribeduser.user_id = %s
        AND NOT news_topic.permissions ='Public'
        """ % user.id
        print liked_sql
        qs = self.get_query_set().extra({'liked':liked_sql, 'disliked':'SELECT not news_linkvote.direction FROM news_linkvote WHERE news_linkvote.link_id = news_relatedlink.related_link_id AND news_linkvote.user_id = %s' % user.id, 'saved':'SELECT 1 FROM news_savedlink WHERE news_savedlink.link_id = news_relatedlink.related_link_id AND news_savedlink.user_id=%s'%user.id, 'can_vote':can_vote_sql})
        return qs


class RelatedLink(models.Model):
    "Links related to a specific link"
    link = models.ForeignKey(Link, related_name = 'link')
    related_link = models.ForeignKey(Link, related_name='related_link_set')
    corelation = models.DecimalField(max_digits = 6, decimal_places = 5)

    objects = RelatedLinkManager()

    class Meta:
        unique_together = ('link', 'related_link')


class RecommendedLinkManager(models.Manager):
    "Manager"
    def get_query_set(self):
        can_vote_sql = """
        SELECT 1 FROM news_topic, news_link
        WHERE news_link.topic_id = news_topic.id
        AND news_link.id = news_recommendedlink.link_id
        AND news_topic.permissions ='Public'
        UNION
        SELECT 1 from news_topic, news_subscribeduser, news_link
        WHERE news_link.topic_id = news_topic.id
        AND news_link.id = news_recommendedlink.link_id
        AND news_subscribeduser.topic_id = news_topic.id
        AND news_subscribeduser.user_id = news_recommendedlink.user_id
        AND NOT news_topic.permissions ='Public'
        """
        qs = super(RecommendedLinkManager, self).get_query_set().extra({'liked':'SELECT news_linkvote.direction FROM news_linkvote WHERE news_linkvote.link_id = news_recommendedlink.link_id AND news_linkvote.user_id = news_recommendedlink.user_id', 'disliked':'SELECT not news_linkvote.direction FROM news_linkvote WHERE news_linkvote.link_id = news_recommendedlink.link_id AND news_linkvote.user_id = news_recommendedlink.user_id', 'saved':'SELECT 1 FROM news_savedlink WHERE news_savedlink.link_id = news_recommendedlink.link_id AND news_savedlink.user_id=news_recommendedlink.user_id', 'can_vote':can_vote_sql})
        return qs


class RecommendedLink(models.Model):
    "Links recommended to an User."
    link = models.ForeignKey(Link)
    user = models.ForeignKey(User)
    recommended_on = models.DateTimeField(auto_now_add = 1)

    objects = RecommendedLinkManager()

    class Meta:
        unique_together = ('link', 'user')


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
        form = DoThreadedComment(user = self.user, link = self.link, parent=self)#prefix = self.id
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
try:
    mptt.register(Comment)
except:
    pass

class CommentVotesManager(VoteManager):
    def do_vote(self, comment, user, direction):
        return super(CommentVotesManager, self).do_vote(user = user, object = comment, direction = direction, voted_class = CommentVote, )


class CommentVote(models.Model):
    "Votes on a comment"
    comment = models.ForeignKey(Comment)
    user = models.ForeignKey(User)
    direction = models.BooleanField(default = True)#Up is true, down is false.
    created_on = models.DateTimeField(auto_now_add = 1)

    objects = CommentVotesManager()

    class Meta:
        unique_together = ('comment', 'user')


VALID_GROUPS = (('Moderator', 'Moderator'), ('Member', 'Member'))
VALID_GROUPS_FLAT = [grp[1] for grp in VALID_GROUPS]

class SubscribedUserManager(models.Manager):
    "Manager for SubscribedUser"
    def subscribe_user(self, user, topic, group='Member'):
        if not group in VALID_GROUPS_FLAT:
            raise InvalidGroup('%s is not a valid group' % group)
        subs = SubscribedUser(user = user, topic = topic, group = group)
        subs.save()
        try:
            invite = Invite.objects.get(user = user, topic = topic)
            invite.delete()
        except Invite.DoesNotExist, e:
            pass
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
    created_on = models.DateTimeField(auto_now_add = 1)
    updated_on = models.DateTimeField(auto_now = 1)
    links_count = models.IntegerField(default = 0)

    objects = TagManager()

    def get_absolute_url(self):
        if self.topic:
            return reverse('topic_tag', kwargs = {'topic_slug':self.topic.slug, 'tag_text':self.text})
        else:
            return reverse('sitewide_tag', kwargs = {'tag_text':self.text})

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

    def get_query_set_with_user(self, user):
        can_vote_sql = """
        SELECT 1 FROM news_topic, news_link
        WHERE news_link.topic_id = news_topic.id
        AND news_link.id = news_linktag.link_id
        AND news_topic.permissions ='Public'
        UNION
        SELECT 1 from news_topic, news_subscribeduser, news_link
        WHERE news_link.topic_id = news_topic.id
        AND news_link.id = news_linktag.link_id
        AND news_subscribeduser.topic_id = news_topic.id
        AND news_subscribeduser.user_id = %s
        AND NOT news_topic.permissions ='Public'
        """ % user.id
        qs = self.get_query_set().extra({'liked':'SELECT news_linkvote.direction FROM news_linkvote WHERE news_linkvote.link_id = news_linktag.link_id AND news_linkvote.user_id = %s' % user.id, 'disliked':'SELECT not news_linkvote.direction FROM news_linkvote WHERE news_linkvote.link_id = news_linktag.link_id AND news_linkvote.user_id = %s' % user.id, 'saved':'SELECT 1 FROM news_savedlink WHERE news_savedlink.link_id = news_linktag.link_id AND news_savedlink.user_id=%s'%user.id, 'can_vote':can_vote_sql})
        return qs


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

    def save(self, *args, **kwargs):
        self.tag.links_count += 1
        self.link.save()
        super(LinkTag, self).save()

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


class EmailActivationKeyManager(models.Manager):
    def save_key(self, user, key):
        act_key = EmailActivationKey(user = user, key = key)
        act_key.save()
        return act_key


class EmailActivationKey(models.Model):
    user = models.ForeignKey(User, unique = True)
    key = models.CharField(max_length = 100)

    objects = EmailActivationKeyManager()


class PasswordResetKeyManager(models.Manager):
    def save_key(self, user, key):
        try:
            act_key = PasswordResetKey.objects.get(user = user)
            act_key.delete()
        except PasswordResetKey.DoesNotExist, e:
            pass
        act_key = PasswordResetKey(user = user, key = key)
        act_key.save()
        return act_key


class PasswordResetKey(models.Model):
    user = models.ForeignKey(User, unique = True)
    key = models.CharField(max_length = 100)

    objects = PasswordResetKeyManager()


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


#Tables where we store scraped Data.
class DiggLinkRecent(models.Model):
    "Links scraped from digg."
    url = models.URLField()
    description = models.TextField()
    title = models.TextField()
    username = models.CharField(max_length = 100)
    submitted_on = models.DateTimeField()
    is_in_main = models.BooleanField(default = False)# Is this scraped link moved to main tables yet?

