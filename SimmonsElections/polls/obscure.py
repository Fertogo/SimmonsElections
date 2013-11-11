# Shift range includes 0-9...A-Z...a-z and some punctuation
shift_range_min = ord('a')
shift_range_max = ord('z')
shift_range_size = ord('z') - ord('a') + 1

def letterToNum(char):
    return ord(char) - shift_range_min
    
def numToLetter(num):
    return chr(num + shift_range_min)
    
def shift_char(c, i):
    return numToLetter((letterToNum(c) + i) % shift_range_size)

def offset(i):
    return ((i + 1) * 7) % shift_range_size

def shift_string(s, left):
    dir = -1 if left else 1
    out = ''
    for (i, c) in enumerate(s):
        if 'a' <= c <= 'z':
            out += shift_char(c, dir * offset(i))
        else:
            out += c
    return out
    
def obscure_str(username):
    return shift_string(str(username), left=False)

def unobscure_str(username):
    return shift_string(str(username), left=True)
