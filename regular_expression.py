with open('wifi.txt', 'r') as f:
    # Read the first line and remove the newline character
    string1 = f.readline().rstrip('\n')
    # Read the second line and remove the newline character
    string2 = f.readline().rstrip('\n')
    
print(string1)
print(string2)