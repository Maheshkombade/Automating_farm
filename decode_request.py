import re
def decode_wifi_id_pass(id,passw):
    special_chars = {
        '%21': '!',
        '%23': '#',
        '%24': '$',
        '%26': '&',
        '%27': "'",
        '%28': '(',
        '%29': ')',
        '%2A': '*',
        '%2B': '+',
        '%2C': ',',
        '%2F': '/',
        '%3A': ':',
        '%3B': ';',
        '%3D': '=',
        '%3F': '?',
        '%40': '@',
        '%5B': '[',
        '%5D': ']',
        '%7B': '{',
        '%7D': '}'
    }

    

    encoded_str_id = id
    encoded_str_pass = passw

    # Use regular expressions to replace percent-encoded sequences with their corresponding characters
    # Define a string
   

    # Replace all "+" with " "
    encoded_str_id = encoded_str_id.replace("+", " ")


    for key, value in special_chars.items():
        encoded_str_id = re.sub(key, value, encoded_str_id)
        encoded_str_pass = re.sub(key, value, encoded_str_pass)

    print(encoded_str_id) # Output: "hi+df@ht"
    print(encoded_str_pass)
    return([encoded_str_id,encoded_str_pass])
decode_wifi_id_pass("hi+%2Bdf%40ht%2B%2B%2B%2B","hi%2Bdf%40ht%2B%2B%2B%2B")