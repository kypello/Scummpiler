import sys, os, re

bits = []
for i in range(2048):
    bits.append(False)

highest_bit_num = 0

for subdir, dirs, files in os.walk(sys.argv[1]):
    for file_name in files:
        file_path = os.path.join(subdir, file_name)

        if not file_path.endswith(".txt"):
            continue
        
        file = open(file_path, 'r')
        script_text = file.read()
        file.close()

        bit_variables = re.findall("Var\[(.*)", script_text)

        for bit_variable in bit_variables:
            print(bit_variable)

            bit_num = int(bit_variable.split(']')[0].split(' ')[0])
            if bit_num > highest_bit_num:
                highest_bit_num = bit_num

print("Highest var num: " + str(highest_bit_num))