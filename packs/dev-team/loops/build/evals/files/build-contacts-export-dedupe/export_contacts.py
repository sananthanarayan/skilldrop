"""Export contacts from a CSV to the mailing tool's format (name,email)."""
import csv
import sys


def read_contacts(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def to_rows(contacts):
    return [(c["first_name"] + " " + c["last_name"], c["email"]) for c in contacts]


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print("usage: export_contacts.py CONTACTS.csv", file=sys.stderr)
        return 2
    contacts = read_contacts(argv[0])
    writer = csv.writer(sys.stdout)
    writer.writerow(["name", "email"])
    for row in to_rows(contacts):
        writer.writerow(row)
    return 0


if __name__ == "__main__":
    sys.exit(main())
