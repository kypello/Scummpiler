import json, googletrans, sys

file = open("all_insult_languages.json", "r")
lines = json.loads(file.read())
file.close()

longest_insult = 0
longest_response = 0
longest_carla_insult = 0

for i in range(0, 16):
    for j in range(0, 5):
        length = len(lines[i][j])
        if length > longest_insult:
            longest_insult = length

for i in range(16, 33):
    for j in range(0, 5):
        length = len(lines[i][j])
        if length > longest_carla_insult:
            longest_carla_insult = length

for i in range(33, 49):
    for j in range(0, 5):
        length = len(lines[i][j])
        if length > longest_response:
            longest_response = length

table = ""

for i in range(0, 17):
    table += "+"
    table += "-" * (longest_insult + 2)
    table += "+"
    table += "-" * (longest_response + 2)
    table += "+"
    table += "-" * (longest_carla_insult + 2)
    table += "+\n"

    for j in range(0, 5):
        table += "| "
        if i < 16:
            table += lines[i][j] + " " * (longest_insult - len(lines[i][j]))
        else:
            table += " " * longest_insult

        table += " | "
        if i < 16:
            table += lines[33 + i][j] + " " * (longest_response - len(lines[33 + i][j]))
        else:
            table += " " * longest_response
        
        table += " | "
        table += lines[16 + i][j] + " " * (longest_carla_insult - len(lines[16 + i][j]))
        table += " |\n"

table += "+"
table += "-" * (longest_insult + 2)
table += "+"
table += "-" * (longest_response + 2)
table += "+"
table += "-" * (longest_carla_insult + 2)
table += "+\n"

print(table)
        

