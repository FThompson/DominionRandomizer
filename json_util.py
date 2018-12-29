"""
This module contains a custom JSON encoder that looks for __json__ functions.

"""

import json


class JSONUnderscoreEncoder(json.JSONEncoder):
    """
    A custom JSON Encoder which uses objects' __json__ functions if present, otherwise uses the default encoder.
    
    """

    def default(self, obj):  # pylint: disable=E0202
        """
        Overrides the standard JSONEncoder's default encoder to check for the callable __json__ attribute.
        
        :return: The JSON encoded object.
        :rtype: str
        """

        if hasattr(obj, '__json__') and callable(getattr(obj, '__json__')):
            return obj.__json__()
        return json.JSONEncoder.default(self, obj)