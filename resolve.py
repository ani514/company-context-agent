import csv

def load_people(path="sample_docs/contacts.csv"):
    with open(path) as f:
        return list(csv.DictReader(f))
    # each row → {"name":..., "email":..., "company":..., "role":...}

def resolve_people(records):
    by_email = {}
    for r in records:
        key = r["email"].lower().strip()

        # Phase 1: first time seeing this email? create the empty entry.
        if key not in by_email:
            by_email[key] = {"email": key, "names": [], "companies": [], "roles": []}

        # Phase 2: add this row's variants (guard against duplicates).
        entry = by_email[key]
        if r["name"] not in entry["names"]:
            entry["names"].append(r["name"])
        if r["company"] not in entry["companies"]:
            entry["companies"].append(r["company"])
        if r["role"] not in entry["roles"]:
            entry["roles"].append(r["role"])

    return list(by_email.values())

if __name__ == "__main__":
    for p in resolve_people(load_people()):
        print(p)