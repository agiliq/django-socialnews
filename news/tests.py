import unittest
from django.contrib.auth.models import User
from models import *
import defaults
from django.db.backends.sqlite3.base import IntegrityError#todo
import random

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
        self.assertRaises(TooLittleKarmaForNewTopic, Topic.objects.create_new_topic, user = self.user, topic_name = 'cpp')
        self.user.get_profile().karma = defaults.KARMA_COST_NEW_TOPIC + 1
        Topic.objects.create_new_topic(user = self.user, topic_name = 'cpp')
        
    def testNameUnq(self):
        self.user.get_profile().karma = 2 * defaults.KARMA_COST_NEW_TOPIC + 1
        Topic.objects.create_new_topic(user = self.user, topic_name = 'cpp')
        self.assertRaises(IntegrityError, Topic.objects.create_new_topic, user = self.user, topic_name = 'cpp')
    
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
        topic = Topic.objects.create_new_topic(user = self.user, topic_name = 'cpp')
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
        link = Link.objects.create_link(url = "http://yahoo.com",user = self.user, topic = self.topic)
        self.assertRaises(IntegrityError, Link.objects.create_link, url = "http://yahoo.com",user = self.user, topic = self.topic)
        
    def testLinkCreation(self):
        self.user.get_profile().karma = defaults.KARMA_COST_NEW_LINK + 1
        link = Link.objects.create_link(url = "http://yahoo.com",user = self.user, topic = self.topic)
        
    def testLinkCreation2(self):
        self.user.get_profile().karma = defaults.KARMA_COST_NEW_LINK - 1
        self.assertRaises(TooLittleKarmaForNewLink, Link.objects.create_link, url = "http://yahoo.com",user = self.user, topic = self.topic)
        
    def testLinkKarmaCost(self):
        self.user.get_profile().karma = defaults.KARMA_COST_NEW_LINK + 1
        prev_karma = self.user.get_profile().karma
        link = Link.objects.create_link(url = "http://yahoo.com", user = self.user, topic = self.topic)
        new_karma = self.user.get_profile().karma
        self.assertEqual(prev_karma - new_karma, defaults.KARMA_COST_NEW_LINK)
        
    def tearDown(self):
        self.user.delete()
        self.profile.delete()
        self.topic.delete()
        
class TestSubscribedUser(unittest.TestCase):
    def setUp(self):
        user = User.objects.create_user(username="demo", email="demo@demo.com", password="demo")
        user.save()
        self.user = user
        profile = UserProfile(user = user, karma = defaults.KARMA_COST_NEW_TOPIC + 1)
        profile.save()
        self.profile = profile
        topic = Topic.objects.create_new_topic(user = self.user, topic_name = 'cpp')
        self.topic = topic
        
        
    def testRequiredFields(self):
        subs = SubscribedUser()
        self.assertRaises(IntegrityError, subs.save)
        subs.user = self.user
        self.assertRaises(IntegrityError, subs.save)
        subs.topic = self.topic
        #self.assertRaises(IntegrityError, subs.save)
        subs.group = 'Owner'
        subs.save()
        
    def testSubsUnq(self):
        subs = SubscribedUser.objects.subscribe_user(user = self.user, topic = self.topic, group = 'Owner')
        self.assertRaises(IntegrityError, SubscribedUser.objects.subscribe_user, user = self.user, topic = self.topic, group = 'Owner')
        
    def testValidGroups(self):
        subs = self.assertRaises(InvalidGroup, SubscribedUser.objects.subscribe_user, user = self.user, topic = self.topic, group = 'Foo')
        
    
    def tearDown(self):
        self.user.delete()
        self.profile.delete()
        self.topic.delete()
        
class TestLinkVotes(unittest.TestCase):
    def setUp(self):
        user = User.objects.create_user(username="demo", email="demo@demo.com", password="demo")
        user.save()
        self.user = user
        profile = UserProfile(user = user, karma = defaults.KARMA_COST_NEW_TOPIC + 1)
        profile.save()
        self.profile = profile
        topic = Topic.objects.create_new_topic(user = self.user, topic_name = 'cpp')
        self.topic = topic
        self.user.get_profile().karma = 2 * defaults.KARMA_COST_NEW_LINK + 1
        link = Link.objects.create_link(url = "http://yahoo.com",user = self.user, topic = self.topic)
        self.link = link
        
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
        
        
    def tearDown(self):
        self.user.delete()
        self.profile.delete()
        self.topic.delete()
        self.link.delete()
        
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
        topic = Topic.objects.create_new_topic(user = self.user, topic_name = 'java', karma_factor = False)
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
        topic = Topic.objects.create_new_topic(user = self.user, topic_name = 'cpp')
        self.topic = topic
        self.user.get_profile().karma = 2 * defaults.KARMA_COST_NEW_LINK + 1
        link = Link.objects.create_link(url = "http://yahoo.com",user = self.user, topic = self.topic)
        self.link = link
        
def __delete_data__(self):
        self.user.delete()
        self.profile.delete()
        self.topic.delete()
        self.link.delete()    
    
    
    