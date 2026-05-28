import re

def _digits(text:str)-> float|None:
     
     pattern= r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?'
     coordinates= re.findall(pattern, text)
     if coordinates:
        print(coordinates[0])
     else:
        print("No digits in string: Mapping->_digits")


_digits('pi value is 3.14')