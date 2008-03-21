import unittest
from django.contrib.auth.models import User
from models import *
import defaults
from django.db.backends.sqlite3.base import IntegrityError#todo
import random
import bforms

"""Test the models."""

class TestTopic(unittest.TestCase):
    def setUp(self):
        user = User.objects.create_user(username="demo", email="demo@demo.com", password="demo")
        user.save()
        self.user = user
        profile = UserProfile(user = user)
        profile.save()
        self.profile = profile
    
    def testRequiredFields(self):
        topic = Topic()
        self.assertRaises(Exception, topic.save, )
        
    def testTopicCreation(self):
        self.assertRaises(TooLittleKarmaForNewTopic, Topic.objects.create_new_topic, user = self.user, full_name = 'A CPP primer', topic_name = 'cpp')
        self.user.get_profile().karma = defaults.KARMA_COST_NEW_TOPIC + 1
        Topic.objects.create_new_topic(user = self.user, full_name = 'A CPP primer', topic_name = 'cpp')
        
    def testNameUnq(self):
        self.user.get_profile().karma = 2 * defaults.KARMA_COST_NEW_TOPIC + 1
        Topic.objects.create_new_topic(user = self.user, full_name = 'A CPP primer', topic_name = 'cpp')
        self.assertRaises(IntegrityError, Topic.objects.create_new_topic, user = self.user, full_name = 'A CPP primer', topic_name = 'cpp')
        
    def testSubScription(self):
        "Test that a subscription gets created."
        self.user.get_profile().karma = 2 * defaults.KARMA_COST_NEW_TOPIC + 1
        self.topic = Topic.objects.create_new_topic(user = self.user, full_name = 'A CPP primer', topic_name = 'cpp')
        subs = SubscribedUser.objects.get(topic = self.topic, user = self.user)
        self.assertEquals(self.user, subs.user)
        self.assertEquals(subs.group, 'Moderator')
    
    def tearDown(self):
        self.user.delete()
        self.profile.delete()
        
class TestLink(unittest.TestCase):
    def setUp(self):
        user = User.objects.create_user(username="demo", email="demo@demo.com", password="demo")
        user.save()
        self.user = user
        profile = UserProfile(user = user, karma = defaults.KARMA_COST_NEW_TOPIC + 1)
        profile.save()
        self.profile = profile
        topic = Topic.objects.create_new_topic(user = self.user, topic_name = 'cpp', full_name='CPP primer')
        self.topic = topic
        
    def testRequiredFields(self):
        link = Link()
        self.assertRaises(Exception, link.save)
        link.user = self.user
        self.assertRaises(Exception, link.save)
        link.url = u'http://yahoo.com'
        self.assertRaises(Exception, link.save)
        link.topic = self.topic
        link.save()
        
    def testLinkUnique(self):
        self.user.get_profile().karma = 2 * defaults.KARMA_COST_NEW_LINK + 1
        link = Link.objects.create_link(url = "http://yahoo.com", text='Yahoo', user = self.user, topic = self.topic)
        self.assertRaises(IntegrityError, Link.objects.create_link, url = "http://yahoo.com", text='Yahoo', user = self.user, topic = self.topic)
        
    def testLinkCreation(self):
        self.user.get_profile().karma = defaults.KARMA_COST_NEW_LINK + 1
        link = Link.objects.create_link(url = "http://yahoo.com",user = self.user, text='Yahoo', topic = self.topic)
        #Created link must be upvoted by the user
        vote = LinkVote.objects.get(link = link, user=self.user)
        self.assertEquals(vote.direction, True)
        
    def testLinkCreation2(self):
        self.user.get_profile().karma = defaults.KARMA_COST_NEW_LINK - 1
        self.assertRaises(TooLittleKarmaForNewLink, Link.objects.create_link, url = "http://yahoo.com", text='Yahoo', user = self.user, topic = self.topic)
        
    def testLinkKarmaCost(self):
        self.user.get_profile().karma = defaults.KARMA_COST_NEW_LINK + 1
        prev_karma = self.user.get_profile().karma
        link = Link.objects.create_link(url = "http://yahoo.com", text='Yahoo', user = self.user, topic = self.topic)
        new_karma = self.user.get_profile().karma
        self.assertEqual(prev_karma - new_karma, defaults.KARMA_COST_NEW_LINK)
        
    def testCommentCount(self):
        "Test the comment count pseudo column."
        self.user.get_profile().karma = defaults.KARMA_COST_NEW_LINK + 1
        self.link = Link.objects.create_link(url = "http://yahoo.com", text='Yahoo', user = self.user, topic = self.topic,)
        com1 = Comment.objects.create_comment(user = self.user, link = self.link, comment_text = '1 coment')
        link = Link.objects.get(pk = self.link.pk)
        self.assertEquals(link.comment_count, 1)
        count = random.randint(5, 10)
        for i in xrange(count):
            Comment.objects.create_comment(user = self.user, link = self.link, comment_text = '1 coment')
        link = Link.objects.get(pk = self.link.pk)
        self.assertEquals(link.comment_count, count + 1)
        
    def testCommentCountMultiUser(self):
        "Comment count pseudo column in presence of multiple users"
        users = []
        self.user.get_profile().karma = defaults.KARMA_COST_NEW_LINK + 1
        self.link = Link.objects.create_link(url = "http://yahoo.com", text='Yahoo', user = self.user, topic = self.topic,)
        for i in xrange(random.randint(5, 10)):
            user = User.objects.create_user(username='testCommentCountMultiUser%s' % i, email='demo@demo.com', password='demo')
            profile = UserProfile(user = user, karma = 0)
            profile.save()
            user.get_profile().karma = defaults.KARMA_COST_NEW_LINK + 1
            users.append(user)
        for user in users:
            Comment.objects.create_comment(user = user, link = self.link, comment_text = '1 coment')
        link =  Link.objects.get(pk = self.link.pk)
        self.assertEquals(link.comment_count, len(users))
        
    def testLiked(self):
        "Test the liked/disliked pseudo column in returned queryset."
        users = []
        self.user.get_profile().karma = defaults.KARMA_COST_NEW_LINK + 1
        self.link = Link.objects.create_link(url = "http://yahoo.com", text='Yahoo', user = self.user, topic = self.topic,)
        for i in xrange(random.randint(5, 10)):
            user = User.objects.create_user(username='testLiked%s' % i, email='demo@demo.com', password='demo')
            profile = UserProfile(user = user, karma = 0)
            profile.save()
            users.append(user)
            self.link.upvote(user)
        link = Link.objects.get_query_set_with_user(self.user).get(pk = self.link.pk)
        self.assertEquals(link.disliked, False)
        self.link.upvote(self.user)
        link = Link.objects.get_query_set_with_user(self.user).get(pk = self.link.pk)
        self.assertEquals(link.liked, True)
        self.assertEquals(link.disliked, False)
        self.link.downvote(self.user)
        link = Link.objects.get_query_set_with_user(self.user).get(pk = self.link.pk)
        self.assertEquals(link.liked, False)
        self.assertEquals(link.disliked, True)
        
        
    def tearDown(self):
        self.user.delete()
        self.profile.delete()
        self.topic.delete()
        
class TestSubscribedUser(unittest.TestCase):
    def setUp(self):
        __populate_data__(self)
        comment = Comment.objects.create_comment(link = self.link, user = self.user, comment_text = 'Foo bar')        
    def tearDown(self):
        __delete_data__(self)
        
    def testSubsUnq(self):
        user = User.objects.create_user(username='testSubsUnq', email='demo@demo.com', password='demo')
        subs = SubscribedUser.objects.subscribe_user(user = user, topic = self.topic, group = 'Member')
        self.assertRaises(IntegrityError, SubscribedUser.objects.subscribe_user, user = user, topic = self.topic, group = 'Member')
        
    def testValidGroups(self):
        self.assertRaises(InvalidGroup, SubscribedUser.objects.subscribe_user, user = self.user, topic = self.topic, group = 'Foo')
        self.assertRaises(InvalidGroup, SubscribedUser.objects.subscribe_user, user = self.user, topic = self.topic, group = 'Viewer')
        
    def testIsModerator(self):
        "Test the values returned ny is_moderator"
        user = User.objects.create_user(username='testIsModerator', email='demo@demo.com', password='demo')
        subs = SubscribedUser.objects.subscribe_user(user = user, topic = self.topic, group = 'Member')
        self.assertEquals(subs.is_moderator(), False)
        subs.group = 'Moderator'
        subs.save()
        self.assertEquals(subs.is_moderator(), True)
        
    def testSetGroup(self):
        "Set group sets the group"
        user = User.objects.create_user(username='testSetGroup', email='demo@demo.com', password='demo')
        subs = SubscribedUser.objects.subscribe_user(user = user, topic = self.topic, group = 'Member')
        subs.set_group('Moderator')
        new_subs = SubscribedUser.objects.get(user = user, topic = self.topic)
        self.assertEquals(subs.group, new_subs.group)
        
    def testDelete(self):
        "Delete should not delete subscription, if you created this topic."
        sub = SubscribedUser.objects.get(topic = self.topic, user=self.user)
        self.assertRaises(CanNotUnsubscribe, sub.delete)
        user = User.objects.create_user(username='testDelete', email='demo@demo.com', password='demo')
        sub = SubscribedUser.objects.subscribe_user(user = user, topic = self.topic, group = 'Member')
        sub.delete()
        
        
class TestLinkVotes(unittest.TestCase):
    def setUp(self):
        __populate_data__(self)
        comment = Comment.objects.create_comment(link = self.link, user = self.user, comment_text = 'Foo bar')        
    def tearDown(self):
        __delete_data__(self)
        
    def testRequiredFields(self):
        vote = LinkVote()
        self.assertRaises(IntegrityError, vote.save)
        
    def testUnqTogether(self):
        vote = LinkVote(user = self.user, link = self.link, direction = True)
        vote.save()
        vote = LinkVote(user=self.user, link=self.link, direction=True)
        self.assertRaises(IntegrityError, vote.save)
        
    def testLinkVotesManager(self):
        vote = LinkVote.objects.do_vote(user = self.user, link = self.link, direction = True)
        prev_count = LinkVote.objects.all().count()
        #Do some random modifications
        for i in xrange(10):
            import random
            dir = random.choice([True, False])
            LinkVote.objects.do_vote(user = self.user, link = self.link, direction = dir)
        new_count = LinkVote.objects.all().count()
        self.assertEquals(prev_count, new_count)
        
class TestTag(unittest.TestCase):
    def setUp(self):
        __populate_data__(self)
    
    def testUnq(self):
        "Two tags with same text can not be sitwide tags."
        tag = Tag(text = 'Asdf')
        tag.save()
        tag = Tag(text = 'Asdf')
        self.assertRaises(Exception, tag.save)
        
    def testUnq2(self):
        "Two tags with same text can not be a per topic tags."
        tag = Tag(text = 'Asdf', topic = self.topic)
        tag.save()
        tag = Tag(text = 'Asdf', topic = self.topic)
        self.assertRaises(IntegrityError, tag.save)
        
    def testUnq3(self):
        "Two tags with same text CAN be 1. sitewide and second per topic tags."
        tag = Tag(text = 'Asdf', topic = self.topic)
        tag.save()
        tag = Tag(text = 'Asdf', topic = None)
        tag.save()
        
    def testManager2(self):
        "Test that manager creates two Tags initially."
        Tag.objects.all().delete()        
        Tag.objects.create_tag('asdf', self.topic)
        count = Tag.objects.all().count()
        self.assertEqual(count, 2)
        
    def testManager(self):
        "Test that calling create tags again will not create new tags"
        Tag.objects.all().delete()
        Tag.objects.create_tag('foo', self.topic)
        prev_count = Tag.objects.all().count()
        Tag.objects.create_tag('foo', self.topic)
        new_count = Tag.objects.all().count()
        self.assertEqual(prev_count, new_count)
        
    def testManager3(self):
        "Creating a new tag with increate count of tags by two."
        Tag.objects.all().delete()
        Tag.objects.create_tag('foo', self.topic)
        prev_count = Tag.objects.all().count()
        Tag.objects.create_tag('bar', self.topic)
        new_count = Tag.objects.all().count()
        self.assertEqual(prev_count + 2, new_count)
        
    def testManager4(self):
        "Creating a tag for an existing tag with new topic will increase count by 1."
        Tag.objects.all().delete()
        topic = Topic.objects.create_new_topic(user = self.user, full_name='A CPP primer', topic_name = 'java', karma_factor = False)
        topic.save()
        Tag.objects.create_tag('bar', self.topic)
        prev_count = Tag.objects.all().count()
        Tag.objects.create_tag('bar', topic)
        new_count = Tag.objects.all().count()
        self.assertEqual(prev_count + 1, new_count)
        
        
    def tearDown(self):
        __delete_data__(self)
    
    
class TestLinkTag(unittest.TestCase):
    def setUp(self):
        __populate_data__(self)
        site_tag, topic_tag = Tag.objects.create_tag('bar', self.topic)
        self.tag = topic_tag
        self.site_tag = site_tag        
    
    def tearDown(self):
        __delete_data__(self)
        self.tag.delete()
        
    def testUnq(self):
        "Test that tag along with link is unique"
        tag = LinkTag(tag = self.tag, link = self.link)
        tag.save()
        tag = LinkTag(tag = self.tag, link = self.link)
        self.assertRaises(IntegrityError, tag.save)
        
    def testLinkTagManager(self):
        "Test that calling LinkTag.objects.tag_link multiple times for a link and tag_text does not create multiple    "
        site_linktag, topic_linktag = LinkTag.objects.tag_link(tag_text = 'foo', link = self.link)
        prev_count = LinkTag.objects.all().count()
        site_linktag, topic_linktag = LinkTag.objects.tag_link(tag_text = 'foo', link = self.link)
        new_count = LinkTag.objects.all().count()
        self.assertEqual(prev_count, new_count)

    def testLinkTagManager2(self):
        "Test that taging a link, creates two link tags, one site wide and other per topic."
        LinkTag.objects.all().delete()
        site_linktag, topic_linktag = LinkTag.objects.tag_link(tag_text = 'foo', link = self.link)
        count = LinkTag.objects.all().count()
        self.assertEqual(count, 2)    
        

        
class TestLinkTagUser(unittest.TestCase):
    def setUp(self):
        __populate_data__(self)
        site_tag, topic_tag = Tag.objects.create_tag('bar', self.topic)
        self.tag = topic_tag
        self.site_tag = site_tag        
    
    def tearDown(self):
        __delete_data__(self)
        self.tag.delete()
        
    def testUnq(self):
        "Test uniqeness constraints for LinkTagUser"
        site_linktag, topic_linktag = LinkTag.objects.tag_link(tag_text = "foo", link = self.link)
        tag = LinkTagUser(link_tag = topic_linktag, user = self.user)
        tag.save()
        tag = LinkTagUser(link_tag = topic_linktag, user = self.user)
        self.assertRaises(IntegrityError, tag.save)
        
    def testLinkTagUserManager(self):
        "Test the manager methods"
        #site_linktag, topic_linktag = LinkTag.objects.tag_link(tag_text = "foo", link = self.link)
        Tag.objects.all().delete()
        LinkTag.objects.all().delete()
        LinkTagUser.objects.all().delete()
        LinkTagUser.objects.tag_link(tag_text = 'foo', link = self.link, user = self.user)
        self.assertEquals(Tag.objects.all().count(), 2)
        self.assertEquals(LinkTag.objects.all().count(), 2)
        self.assertEquals(LinkTagUser.objects.all().count(), 1)
        
    def testLinkTagUserManagerMultiUser(self):
        "LinkTagUser with multiple users"
        Tag.objects.all().delete()
        LinkTag.objects.all().delete()
        LinkTagUser.objects.all().delete()
        LinkTagUser.objects.tag_link(tag_text = 'foo', link = self.link, user = self.user)
        self.assertEquals(Tag.objects.all().count(), 2)
        self.assertEquals(LinkTag.objects.all().count(), 2)
        self.assertEquals(LinkTagUser.objects.all().count(), 1)
        user = User.objects.create_user(username='testLinkTagUserManagerMultiUser', email='demo@demo.com', password='demo')
        LinkTagUser.objects.tag_link(tag_text = 'foo', link = self.link, user = user)
        self.assertEquals(Tag.objects.all().count(), 2)
        self.assertEquals(LinkTag.objects.all().count(), 2)
        self.assertEquals(LinkTagUser.objects.all().count(), 2)
        
        
class TestTagging(unittest.TestCase):
    "Test that tagging works correctly as a whole."
    def setUp(self):
        __populate_data__(self)    
    
    def tearDown(self):
        __delete_data__(self)
        
    def testTagLink(self):
        "Tag a link, get it back."
        LinkTagUser.objects.tag_link(tag_text = 'foo', link = self.link, user = self.user)
        tag = Tag.objects.get(text = 'foo', topic__isnull = True)
        self.assertEquals(tag.linktag_set.all()[0].link, self.link)
        
    def testTagLink2(self):
        "Tag a link multiple times, see that it is tagged only once for topic and once for sitewide."
        import random
        LinkTagUser.objects.tag_link(tag_text = 'foo', link = self.link, user = self.user)
        for i in xrange(random.randint(5, 10)):
            LinkTagUser.objects.tag_link(tag_text = 'foo', link = self.link, user = self.user)
        self.assertEquals(self.link.linktag_set.filter(tag__topic__isnull = True).count(), 1)
        self.assertEquals(self.link.linktag_set.filter(tag__topic__isnull = False).count(), 1)
        #self.assertEquals(self.link.linktag_set.filter(tag = self.tag).count(), 1)
        
class TestVoting(unittest.TestCase):
    "Test the voting system."
    def setUp(self):
        __populate_data__(self)
    
    def tearDown(self):
        __delete_data__(self)
        
    def testUpvote(self):
        "Test that upvoting a link increases the liked_by_count by 1, and does not increase the disliked_by_count"
        prev_liked_by_count = self.link.liked_by_count
        prev_disliked_by_count = self.link.disliked_by_count
        self.link.upvote(self.user)
        new_liked_by_count = self.link.liked_by_count
        self.assertEquals(prev_liked_by_count + 1, new_liked_by_count)
        self.assertEquals(prev_disliked_by_count,  self.link.disliked_by_count)
        
    def testUpvoteMultiple(self):
        "Test that upvoting a link, multiple times increases the liked_by_count by 1 only"
        prev_liked_by_count = self.link.liked_by_count
        self.link.upvote(self.user)
        self.link.upvote(self.user)
        self.link.upvote(self.user)
        new_liked_by_count = self.link.liked_by_count
        self.assertEquals(prev_liked_by_count + 1, new_liked_by_count)
        import random
        for i in xrange(random.randint(5, 10)):
            self.link.upvote(self.user)
        new_liked_by_count2 = self.link.liked_by_count
        self.assertEquals(prev_liked_by_count + 1, new_liked_by_count2)
        
    def testDownvote(self):
        "Test that down a link increases the disliked_by_count by 1, and does not affect the liked_by_count"
        prev_liked_by_count = self.link.liked_by_count
        prev_disliked_by_count = self.link.disliked_by_count
        self.link.downvote(self.user)
        new_disliked_by_count = self.link.disliked_by_count
        self.assertEquals(prev_disliked_by_count + 1, new_disliked_by_count)
        self.assertEquals(prev_liked_by_count, self.link.liked_by_count)
        
    def testDownvoteMultiple(self):
        "Test that down a link, multiple times increases the disliked_by_count by 1 only"
        prev_disliked_by_count = self.link.disliked_by_count
        self.link.downvote(self.user)
        self.link.downvote(self.user)
        self.link.downvote(self.user)
        new_disliked_by_count = self.link.disliked_by_count
        self.assertEquals(prev_disliked_by_count + 1, new_disliked_by_count)
        for i in xrange(random.randint(5, 10)):
            self.link.downvote(self.user)
        new_disliked_by_count2 = self.link.disliked_by_count
        self.assertEquals(prev_disliked_by_count + 1, new_disliked_by_count2)
        
    def testLinkVote(self):
        "Voting any number of times creates a single LinkVote object."
        LinkVote.objects.all().delete()
        self.link.upvote(self.user)
        self.assertEquals(LinkVote.objects.all().count(), 1)
        for i in xrange(random.randint(5, 10)):
            self.link.upvote(self.user)
        self.assertEquals(LinkVote.objects.all().count(), 1)
        self.link.downvote(self.user)
        self.assertEquals(LinkVote.objects.all().count(), 1)
        for i in xrange(random.randint(5, 10)):
            self.link.downvote(self.user)
        self.assertEquals(LinkVote.objects.all().count(), 1)
        
    def testMultipleUser(self):
        "Voting with multiple users."
        LinkVote.objects.all().delete()
        prev_liked_by_count = self.link.liked_by_count
        prev_disliked_by_count = self.link.disliked_by_count
        users = []
        for i in xrange(random.randint(5, 10)):
            user = User.objects.create_user(username = 'demo%s'%i, password='demo', email='demo@demo.com')
            users.append(user)
        for user in users:
            self.link.upvote(user)
        users2 = []
        for i in xrange(random.randint(5, 10)):
            user = User.objects.create_user(username = 'demo_%s'%i, password='demo', email='demo@demo.com')
            users2.append(user)
        for user in users2:
            self.link.downvote(user)
        self.assertEquals(prev_disliked_by_count + len(users2), self.link.disliked_by_count)
        self.assertEquals(len(users)+len(users2), LinkVote.objects.all().count())
        
        
        
    def testUpDownVote(self):
        """Upvote and downvote play nice with each other.
        Upvote and check that liked_by _count inc by 1, disliked by count remains old value.
        Down vote and check that liked by count gets to the old value, disliked_by_count increases by 1.
        Upvote and check that liked by count increases by 1, dislked_cnt get to old value.
        """
        prev_liked_by_count = self.link.liked_by_count
        prev_disliked_by_count = self.link.disliked_by_count
        self.link.upvote(self.user)
        new_liked_by_count = self.link.liked_by_count
        new_disliked_by_count = self.link.disliked_by_count
        self.assertEquals(prev_liked_by_count + 1, new_liked_by_count)
        self.assertEquals(prev_disliked_by_count, new_disliked_by_count)
        self.link.downvote(self.user)
        self.assertEquals(prev_liked_by_count, self.link.liked_by_count)
        self.assertEquals(prev_disliked_by_count + 1, self.link.disliked_by_count)
        self.link.upvote(self.user)
        self.assertEquals(prev_liked_by_count + 1, self.link.liked_by_count)
        self.assertEquals(prev_disliked_by_count, self.link.disliked_by_count)
        
    def testResetVote(self):
        "Vote and then reset"
        prev_liked_by_count = self.link.liked_by_count
        prev_disliked_by_count = self.link.disliked_by_count
        self.link.upvote(self.user)
        self.link.reset_vote(self.user)
        self.assertEquals(prev_liked_by_count, self.link.liked_by_count)
        self.assertEquals(prev_disliked_by_count, self.link.disliked_by_count)
        self.link.upvote(self.user)
        self.link.reset_vote(self.user)
        self.assertEquals(prev_liked_by_count, self.link.liked_by_count)
        self.assertEquals(prev_disliked_by_count, self.link.disliked_by_count)
        for i in xrange(random.randint(5, 10)):
            self.link.upvote(self.user)
        for i in xrange(random.randint(5, 10)):
            self.link.reset_vote(self.user)
        self.assertEquals(prev_liked_by_count, self.link.liked_by_count)
        self.assertEquals(prev_disliked_by_count, self.link.disliked_by_count)
        for i in xrange(random.randint(5, 10)):
            self.link.upvote(self.user)
        for i in xrange(random.randint(5, 10)):
            pass
            #self.link.downvote(self.user)
        for i in xrange(random.randint(5, 10)):
            self.link.reset_vote(self.user)
        self.assertEquals(prev_liked_by_count, self.link.liked_by_count)
        self.assertEquals(prev_disliked_by_count, self.link.disliked_by_count)
        
    def testVisisblePoints(self):
        "TEst visible points pseudo column"
        self.link.upvote(self.user)
        link = Link.objects.get(pk = self.link.pk)
        self.assertEquals(link.visible_points, 1)
        self.link.downvote(self.user)
        link = Link.objects.get(pk = self.link.pk)
        self.assertEquals(link.visible_points, -1)
        for i in xrange(random.randint(5, 10)):
            self.link.upvote(self.user)
        link = Link.objects.get(pk = self.link.pk)
        self.assertEquals(link.visible_points, 1)
        
    def testResetVoteMultiUser(self):
        prev_liked_by_count = self.link.liked_by_count
        prev_disliked_by_count = self.link.disliked_by_count
        users = []
        for i in xrange(random.randint(5, 10)):
            user = User.objects.create_user(username = 'demo%stestResetVoteMultiUser'%i, password='demo', email='demo@demo.com')
            users.append(user)
        for user in users:
            self.link.upvote(user)
        for i, user in enumerate(users):
            self.link.reset_vote(user)
            self.assertEqual(prev_liked_by_count + len(users) - i - 1, self.link.liked_by_count)
        for user in users:
            self.link.downvote(user)
        for i, user in enumerate(users):
            self.link.reset_vote(user)
            self.assertEqual(prev_disliked_by_count + len(users) - i - 1, self.link.disliked_by_count)
            
    def testObjectReturned(self):
        "Upvote, downvote and reset, return a LInkVote object"
        vote = self.link.upvote(self.user)
        self.assertEquals(type(vote), LinkVote)
        vote = self.link.downvote(self.user)
        self.assertEquals(type(vote), LinkVote)
        vote = self.link.reset_vote(self.user)
        self.assertEquals(type(vote), LinkVote)
        
        
        

            
class TestPoints(unittest.TestCase):
    "Test the points system"
    def setUp(self):
        __populate_data__(self)
    def tearDown(self):
        __delete_data__(self)
    
    def testSubmissions(self):
        "Submitted stories start with the points of the submitter."
        link = Link.objects.create_link(user = self.user, topic=self.topic, url='http://testSubmissions.com/', text='testSubmissions')
        self.assertEquals(self.user.get_profile().karma, link.points)
        
    def testUpvote(self):
        "Upvoting increases the points, by karma if it is less than max_change"
        profile = self.user.get_profile()
        profile.karma = random.randint(2, defaults.MAX_CHANGE_PER_VOTE)
        profile.save()
        link = Link.objects.create_link(user = self.user, topic=self.topic, url='http://testUpvote.com/', text='testUpvote')
        old_points = link.points
        link.upvote(self.user)
        new_points = link.points
        self.assertEquals(old_points+profile.karma, new_points)
        
    def testMultipleUpvotes(self):
        "Multiple upvotes do not change karma"
        profile = self.user.get_profile()
        profile.karma = random.randint(2, defaults.MAX_CHANGE_PER_VOTE)
        profile.save()
        link = Link.objects.create_link(user = self.user, topic=self.topic, url='http://testUpvote.com/', text='testUpvote')
        old_points = link.points
        link.upvote(self.user)
        new_points = link.points
        self.assertEquals(old_points+profile.karma, new_points)
        for i in xrange(random.randint(5, 10)):
            link.upvote(self.user)
        new_points2 = link.points
        self.assertEquals(new_points2, new_points)
        
    def testUpvoteNegative(self):
        "If users karma is negative, it has no effect on points"
        profile = self.user.get_profile()
        profile.karma = -10
        profile.save()
        link = Link.objects.create_link(user = self.user, topic=self.topic, url='http://testUpvote.com/', text='testUpvote')
        old_points = link.points
        link.upvote(self.user)
        new_points = link.points
        self.assertEquals(old_points, new_points)
        
    def testUpvoteHigKarma(self):
        "If karma is greater tahn max change it, only changes the value till max change"
        profile = self.user.get_profile()
        profile.karma = defaults.MAX_CHANGE_PER_VOTE + 100
        profile.save()
        link = Link.objects.create_link(user = self.user, topic=self.topic, url='http://testUpvote.com/', text='testUpvote')
        old_points = link.points
        link.upvote(self.user)
        new_points = link.points
        self.assertEquals(old_points+defaults.MAX_CHANGE_PER_VOTE, new_points)
        
        
        
class TestComents(unittest.TestCase):
    def setUp(self):
        __populate_data__(self)
        comment = Comment.objects.create_comment(link = self.link, user = self.user, comment_text = 'Foo bar')
        self.comment = comment
        
    def tearDown(self):
        __delete_data__(self)
        self.comment.delete()
        
        
    def testUnq(self):
        "Test uniwueness constraints"
        vote = CommentVote(comment = self.comment, user = self.user, direction = True)
        vote.save()
        vote2 = CommentVote(comment = self.comment, user = self.user, direction = True)
        self.assertRaises(IntegrityError, vote2.save)
        
    def testUpvote(self):
        "Multiple upvotes increase points by one only."
        comment = self.comment
        vote = comment.upvote(self.user)
        self.assertEqual(comment.points, 1)
        vote = comment.upvote(self.user)
        self.assertEqual(comment.points, 1)
        for i in xrange(random.randint(5, 10)):
            vote = comment.upvote(self.user)
            self.assertEqual(comment.points, 1)
            
    def testDownVote(self):
        "Multiple upvotes decrease points by one only."
        comment = self.comment
        vote = comment.downvote(self.user)
        self.assertEqual(comment.points, -1)
        vote = comment.downvote(self.user)
        self.assertEqual(comment.points, -1)
        for i in xrange(random.randint(5, 10)):
            vote = comment.downvote(self.user)
            self.assertEqual(comment.points, -1)
            
    def testUpvoteMultipleUser(self):
        "Upvote in presence of multiple users."
        users = []
        for i in xrange(random.randint(5, 10)):
            user = User.objects.create_user(username='demotestUpvoteMultipleUser%s'%i, password = 'demo', email='demo@demo.com')
            users.append(user)
        for user in users:
            self.comment.upvote(user)
        self.assertEquals(self.comment.points, len(users))
        
    def testDownVoteMultipleUser(self):
        "Downvote in presence of multiple users."
        users = []
        for i in xrange(random.randint(5, 10)):
            user = User.objects.create_user(username='demotestDownvoteMultipleUser%s'%i, password = 'demo', email='demo@demo.com')
            users.append(user)
        for user in users:
            self.comment.downvote(user)
        self.assertEquals(self.comment.points, -len(users))
        
    def testUpDownVote(self):
        "Upvote and downvote play nice with each other."
        self.comment.upvote(self.user)
        self.assertEquals(self.comment.points, 1)
        self.comment.downvote(self.user)
        self.assertEquals(self.comment.points, -1)
        for i in xrange(random.randint(5, 10)):
            self.comment.upvote(self.user)
            self.assertEquals(self.comment.points, 1)
        for i in xrange(random.randint(5, 10)):
            self.comment.downvote(self.user)
            self.assertEquals(self.comment.points, -1)
            
    def testResetVote(self):
        "Test reseting of votes."
        comment = self.comment
        comment.upvote(self.user)
        self.assertEquals(self.comment.points, 1)
        comment.reset_vote(self.user)
        self.assertEquals(self.comment.points, 0)
        comment.downvote(self.user)
        self.assertEquals(self.comment.points, -1)
        comment.reset_vote(self.user)
        self.assertEquals(self.comment.points, 0)
        
    def testResetVoteMultiUser(self):
        "Reseting does not reset the vote of others."
        comment = self.comment
        users = []
        for i in xrange(random.randint(5, 10)):
            user = User.objects.create_user(username='testResetVoteMultiUser%s'%i, password = 'demo', email='demo@demo.com')
            users.append(user)
        for user in users:
            comment.upvote(user)
        for i, user in enumerate(users):
            comment.reset_vote(user)
            self.assertEquals(comment.points, len(users) - i - 1)
        

def __populate_data__(self):
        user = User.objects.create_user(username="demo", email="demo@demo.com", password="demo")
        user.save()
        self.user = user
        profile = UserProfile(user = user, karma = defaults.KARMA_COST_NEW_TOPIC + 1)
        profile.save()
        self.profile = profile
        topic = Topic.objects.create_new_topic(user = self.user, topic_name = 'cpp', full_name='CPP primer')
        self.topic = topic
        self.user.get_profile().karma = 2 * defaults.KARMA_COST_NEW_LINK + 1
        link = Link.objects.create_link(url = "http://yahoo.com", text='Yahoo', user = self.user, topic = self.topic)
        self.link = link
        
def __delete_data__(self):
        self.user.delete()
        self.profile.delete()
        self.topic.delete()
        self.link.delete()
        
"""Test the forms."""

class TestNewTopic(unittest.TestCase):
    def setUp(self):
        __populate_data__(self)
        comment = Comment.objects.create_comment(link = self.link, user = self.user, comment_text = 'Foo bar')        
    def tearDown(self):
        __delete_data__(self)
        
    def testCreatesTopic(self):
        "Sanity check on created Topic."
        profile = self.user.get_profile()
        profile.karma = defaults.KARMA_COST_NEW_TOPIC + 1
        profile.save()
        form = bforms.NewTopic(user = self.user, data = {'topic_name':'testCreatesTopic', 'topic_fullname':'testCreatesTopic'})
        status = form.is_valid()
        self.assertEqual(status, True)
        topic = form.save()
        self.assertEquals(topic.name, 'testCreatesTopic')
        self.assertEquals(topic.created_by, self.user)
        
    def testInvalidOnExisting(self):
        "Do not allow creating a topic, if a topic with same name exists."
        profile = self.user.get_profile()
        profile.karma = defaults.KARMA_COST_NEW_TOPIC + 1
        profile.save()
        topic = Topic.objects.create_new_topic(user = self.user, full_name='A CPP primer', topic_name = 'testInvalidOnExisting')
        form = bforms.NewTopic(user = self.user, data = {'topic_name':'testInvalidOnExisting'})
        status = form.is_valid()
        self.assertEqual(status, False)
        topic.delete()
        
    def testInvalidOnLessKarma(self):
        "Do not allow creating new topic if too litle karma"
        profile = self.user.get_profile()
        profile.karma = defaults.KARMA_COST_NEW_TOPIC - 2
        profile.save()
        form = bforms.NewTopic(user = self.user, data = {'topic_name':'testInvalidOnLessKarma'})
        status = form.is_valid()
        self.assertEqual(status, False)
        
class TestNewLink(unittest.TestCase):
    "Test the new link form"
    def setUp(self):
        __populate_data__(self)
        comment = Comment.objects.create_comment(link = self.link, user = self.user, comment_text = 'Foo bar')        
    def tearDown(self):
        __delete_data__(self)
        
    def testCreateNewLink(self):
        "sanity check on creating a new link using this form"
        profile = self.user.get_profile()
        profile.karma = defaults.KARMA_COST_NEW_LINK + 1
        profile.save()
        form  = bforms.NewLink(user = self.user,topic = self.topic,data = dict(url='http://testCreateNewLink.com', text='123'))
        self.assertEqual(form.is_bound, True)
        self.assertEqual(form.is_valid(), True)
        
        link = form.save()
        self.assertEqual(link.url, 'http://testCreateNewLink.com')
        self.assertEqual(link.text, '123')
        self.assertEqual(link.user, self.user)
        self.assertEqual(link.topic, self.topic)
        
    def testInvalidOnExisting(self):
        Link.objects.create_link(url = 'http://testInvalidOnExisting.com', user=self.user, topic=self.topic, text='Yahoo')
        profile = self.user.get_profile()
        profile.karma = defaults.KARMA_COST_NEW_LINK + 1
        profile.save()
        form  = bforms.NewLink(user = self.user,topic = self.topic,data = dict(url='htp://testInvalidOnExisting.com'))
        self.assertEqual(form.is_bound, True)
        self.assertEqual(form.is_valid(), False)
        
    def testInvalidOnLessKarma(self):
        profile = self.user.get_profile()
        profile.karma = defaults.KARMA_COST_NEW_LINK  - 1
        profile.save()
        form  = bforms.NewLink(user = self.user,topic = self.topic,data = dict(url='htp://testInvalidOnLessKarma.com'))
        self.assertEqual(form.is_bound, True)
        self.assertEqual(form.is_valid(), False)
        
class TestDoComment(unittest.TestCase):
    def setUp(self):
        __populate_data__(self)
    def tearDown(self):
        __delete_data__(self)
        
    def testCreateNewComment(self):
        "sanity check that new comment, creates the comment."
        form = bforms.DoComment(user = self.user, link = self.link, data = dict(text = '123'))
        self.assertEquals(form.is_bound, True)
        self.assertEquals(form.is_valid(), True)
        comment = form.save()
        self.assertEquals(comment.user, self.user)
        self.assertEquals(comment.link, self.link)
        self.assertEquals(comment.comment_text, '123')
        
class TestAddTag(unittest.TestCase):
    def setUp(self):
        __populate_data__(self)
    def tearDown(self):
        __delete_data__(self)
    
    def testCreateNewTag(self):
        "Test that the tag objects get created."
        form = bforms.AddTag(link = self.link, user = self.user, data = dict(tag='asdf'))
        self.assertEquals(form.is_bound, True)
        self.assertEquals(form.is_valid(), True)
        Tag.objects.all().delete()
        LinkTag.objects.all().delete()
        tag = form.save()
        self.assertEqual(Tag.objects.all().count(), 2)
        self.assertEqual(LinkTag.objects.all().count(), 2)
        self.assertEqual(LinkTagUser.objects.all().count(), 1)
        
    def testCreateExistingTag(self):
        "Exitsing tags do noot get created again"        
        form = bforms.AddTag(link = self.link, user = self.user, data = dict(tag='asdf'))
        self.assertEquals(form.is_valid(), True)
        tag = form.save()
        bforms.AddTag(link = self.link, user = self.user, data = dict(tag='asdf'))
        count1 = Tag.objects.all().count()
        count2 = LinkTag.objects.all().count()
        count3 = LinkTagUser.objects.all().count()
        self.assertEquals(form.is_valid(), True)
        tag = form.save()
        self.assertEqual(Tag.objects.all().count(), count1)
        self.assertEqual(LinkTag.objects.all().count(), count2)
        self.assertEqual(LinkTagUser.objects.all().count(), count3)
        
    def testCreateExistingNewUser(self):
        "For new user a tag gets created"
        form = bforms.AddTag(link = self.link, user = self.user, data = dict(tag='asdf'))
        self.assertEquals(form.is_valid(), True)
        tag = form.save()
        user = User.objects.create_user(username = 'testCreateExistingNewUser', email='demo@demo.com', password='demo')
        bforms.AddTag(link = self.link, user = user, data = dict(tag='asdf'))
        count1 = Tag.objects.all().count()
        count2 = LinkTag.objects.all().count()
        count3 = LinkTagUser.objects.all().count()
        self.assertEquals(form.is_valid(), True)
        tag = form.save()
        self.assertEqual(Tag.objects.all().count(), count1)
        self.assertEqual(LinkTag.objects.all().count(), count2)
        self.assertEqual(LinkTagUser.objects.all().count(), count3 + 1)
        
#Test the helper function
import helpers
import exceptions
class TestGetTopic(unittest.TestCase):
    "Test method get topic"
    def setUp(self):
        __populate_data__(self)
    def tearDown(self):
        __delete_data__(self)
        
    def testValidTopic(self):
        "Returns a topic on get_topic, with a valid topic."
        topic = helpers.get_topic(None, self.topic.name)
        self.assertEquals(topic, self.topic)
        
    def testInValidTopic(self):
        "Raises exceptions on invalid topic"
        self.assertRaises(exceptions.NoSuchTopic, helpers.get_topic, None, '1234567aa')
        
#Test the views
from django.test.client import Client
class TestTopicMain(unittest.TestCase):
    def setUp(self):
        self.c = Client()
        self.user = UserProfile.objects.create_user('TestTopicMain', 'demo@demo.com', 'demo')
        
    def tearDown(self):
        self.user.delete()
    
    def testResponseDummy(self):
        "Test dumy send the correct response."
        resp = self.c.get('/dummy/')
        self.assertEqual(resp.status_code, 200)
        
    def testMain(self):
        "Test main_page sends the correct response."
        resp = self.c.get('/')
        self.assertEqual(resp.status_code, 200)
        
    def testTopicMain(self):
        "Test topic main sends a correct response."
        topic = Topic.objects.create_new_topic(topic_name='wiki', full_name='Wiki pedia', user=self.user)
        resp = self.c.get('/wiki/')
        self.assertEqual(resp.status_code, 200)
        resp = self.c.get('/doesnotexits/')
        self.assertEqual(resp.status_code, 302)
        topic.delete()
        
    def testSubmitLinkGet(self):
        "Simulate get on submit_link"
        topic = Topic.objects.create_new_topic(topic_name='wiki', full_name='Wiki pedia', user=self.user)
        resp = self.c.get('/wiki/submit/')
        self.assertEqual(resp.status_code, 302)
        self.c.login(username='TestTopicMain', password='demo')
        resp = self.c.get('/wiki/submit/')
        self.assertEqual(resp.status_code, 200)
        topic.delete()
        
    def testSubmitLinkPost(self):
        import pdb
        pdb.set_trace()
        topic = Topic.objects.create_new_topic(topic_name='wiki', full_name='Wiki pedia', user=self.user)
        resp = self.c.post('/wiki/submit/', {'url':'http://yahoomail.com/', 'text':'Mail'})
        self.assertEquals(resp.status_code, 302)
        link = Link.objects.get(url = 'http://yahoomail.com/', topic=topic)
        self.assertEquals(link.text, 'Mail')
        
        
        
        
        
        
        
        
        
        
        
    
    