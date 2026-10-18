# makes the tea & setup rota for rehearsals
import itertools

DATES = ["7 Nov", "14 Nov", "21 Nov", "28 Nov", "5 Dec"]

with open("members.txt") as f:
    members = [line.strip() for line in f if line.strip()]

people = itertools.cycle(members)
for d in DATES:
    a, b = next(people), next(people)
    print(f"{d}: {a} & {b}")
