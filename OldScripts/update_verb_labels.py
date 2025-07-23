import sys, os

def update_labels(input_path):
    for subdir, dirs, files in os.walk(input_path):
        for file_name in files:
            print(file_name)
            if file_name == "VERB.txt":
                verb_file_path = os.path.join(subdir, file_name)
                verb_file = open(verb_file_path, 'r')
                verb_text = verb_file.read()
                verb_file.close()

                verb_label_table = {}
                verb_counts = {}

                verb_counts["5A"] = 0
                verb_counts["5B"] = 0
                verb_counts["50"] = 0
                verb_counts["FF"] = 0

                lines = verb_text.splitlines()
                
                i = len(lines) - 1

                for line in verb_text.splitlines():
                    if line[:7] == "  5A - ":
                        if verb_counts["5A"] == 0:
                            verb_label_table[line[7:]] = "highlight"
                        else:
                            verb_label_table[line[7:]] = "highlight_" + str(verb_counts["5A"])
                        verb_counts["5A"] += 1
                    if line[:7] == "  5B - ":
                        if verb_counts["5B"] == 0:
                            verb_label_table[line[7:]] = "assign_icon"
                        else:
                            verb_label_table[line[7:]] = "assign_icon_" + str(verb_counts["5B"])
                        verb_counts["5B"] += 1
                    if line[:7] == "  50 - ":
                        if verb_counts["50"] == 0:
                            verb_label_table[line[7:]] = "receive_item"
                        else:
                            verb_label_table[line[7:]] = "receive_item_" + str(verb_counts["50"])
                        verb_counts["50"] += 1
                    if line[:7] == "  FF - ":
                        if verb_counts["FF"] == 0:
                            verb_label_table[line[7:]] = "default"
                        else:
                            verb_label_table[line[7:]] = "default_" + str(verb_counts["FF"])
                        verb_counts["FF"] += 1
                
                for label in verb_label_table:
                    verb_text = verb_text.replace(label, verb_label_table[label])
                
                verb_file = open(verb_file_path, 'w')
                verb_file.write(verb_text)
                verb_file.close()

update_labels(sys.argv[1])