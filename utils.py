import urllib

class DummyTag:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

def create_dummy_tags(tag_list):
    """
    Given a space-delimited string of tag names, creates a list of
    dummy tag objects which contain name attributes.

    This can be used to reuse an item's list of tag names for display
    purposes instead of loading tags from the database.
    """
    tag_names = tag_list.split()
    return [DummyTag(tag_name) for tag_name in tag_names]