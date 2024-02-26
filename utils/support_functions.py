def check_column_limit(list, limit):
    """ 
     Check that any number of the list surpasses the limit given
    """
    for number in list:
        if number > limit:
            return False  
    return True  