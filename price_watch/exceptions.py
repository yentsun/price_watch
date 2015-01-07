class MultidictError(Exception):
    """
    Raised by `multidict_to_list` when tuples have unequal
    number of values
    """
    def __init__(self):
        message = u'Bad multidict: value counts not equal'
        Exception.__init__(self, message)