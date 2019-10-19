
table = {}

for i in range(10000000):
    h = hash(i)

    if h not in table:
        table[h] = []

    table[h].append(i)

for h in table:
    if len(table[h]) >= 2:
        print(table[h])
