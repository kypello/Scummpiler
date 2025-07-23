array_a = [0] * 41
array_b = [0] * 41

answers = [0] * 102

for i in range(1, 17):
    answers[i * 3] = i

for i in range(1, 17):
    answers[(16 + i) * 3] = i



answers[33 * 3 + 1] = 16
answers[33 * 3 + 2] = 4
answers[21 * 3 + 1] = 16
answers[19 * 3 + 1] = 11
answers[25 * 3 + 1] = 14

print(answers)

insults = ["END for you", "shish kebab", "handkerchief blood", "fall at my feet",
    "smart dog", "puke", "nobody's drawn blood", "dairy farmer",
    "scar on my face", "diapers", "contemptible sneak", "no match for brains",
    "manners of beggar", "insolence", "no words", "polite apes",
    "sharp lesson", "tongue sharper than sword", "name is feared", "enemies run away",
    "met a coward", "marry a pig", "no one will catch me", "milk blood",
    "covered in blood", "escape boat", "famous sword", "master swordsman",
    "stupid words", "pain in backside", "no clever moves", "filth and stupidity",
    "passed out on tavern"]

responses = ["TIP for you", "feather duster", "janitor job", "before breath",
    "taught you everything", "someone already did", "run fast", "appropriate cow",
    "nose picking", "borrow one", "no one's heard of you", "I'd be in trouble",
    "comfortable with me", "hemorrhoids", "you never learned", "family reunion"]

for i in range(0, 33):
    print(insults[i])
    for j in range(0, 3):
        possible_answer = answers[(i + 1) * 3 + j]
        if possible_answer != 0:
            print("\t" + responses[possible_answer - 1])
    print("")

