class NoSuchTopic(Exception):
    pass

class PrivateTopicNoAccess(Exception):
    pass

class MemberTopicNotSubscribed(Exception):
    pass