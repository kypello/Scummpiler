import sys

def separate(path):
    file = open(path, 'r')
    text = file.read()
    file.close()

    text = text.replace("\\xFF\\x03", "\\xFF\\x03\n")

    file = open(path, 'w')
    file.write(text)
    file.close()

def unseparate(path):
    file = open(path, 'r')
    text = file.read()
    file.close()

    text = text.replace("\\xFF\\x03\n", "\\xFF\\x03")

    file = open(path, 'w')
    file.write(text)
    file.close()

if sys.argv[1] == "s":
    separate(sys.argv[2])
if sys.argv[1] == "u":
    unseparate(sys.argv[2])