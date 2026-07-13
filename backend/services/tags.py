from extensions import db


def get_tags(contact):
    if not contact or not contact.tags:
        return []
    return [t.strip().lower() for t in contact.tags.split(",") if t.strip()]


def set_tags(contact, tags_str):
    if contact:
        contact.tags = tags_str
        db.session.commit()


def replace_tag(contact, match_tags, new_tag):
    if not contact:
        return
    raw_tags = [t.strip() for t in (contact.tags or "").split(",") if t.strip()]
    match_set = {m.lower() for m in match_tags}
    new_tags = []
    replaced = False
    for t in raw_tags:
        if t.lower() in match_set:
            if not replaced:
                new_tags.append(new_tag)
                replaced = True
        else:
            new_tags.append(t)
    if not replaced:
        new_tags.append(new_tag)
    contact.tags = ", ".join(new_tags)
    db.session.commit()


def add_tag(contact, new_tag):
    if not contact:
        return
    raw_tags = [t.strip() for t in (contact.tags or "").split(",") if t.strip()]
    if any(t.lower() == new_tag.lower() for t in raw_tags):
        return
    raw_tags.append(new_tag)
    contact.tags = ", ".join(raw_tags)
    db.session.commit()


def normalize_tags(tags):
    return {t.strip().lower() for t in (tags or []) if t and t.strip()}


# Contacts tagged with exactly {lead, pkd workshop 18/06, group-<letter>} (a
# through q) are hidden from the Contacts list and from campaign
# audiences/sends. Contacts with additional tags on top of this combo, or
# missing one of these three, are left alone.
_HIDDEN_EXACT_TAG_SETS = [
    {"lead", "pkd workshop 18/06", f"group-{letter}"}
    for letter in "abcdefghijklmnopq"
]


def is_hidden(contact):
    return set(get_tags(contact)) in _HIDDEN_EXACT_TAG_SETS


def filter_contacts_by_tags(contacts, required_tags, match_type="any"):
    """Filter contacts against a required tag set.

    match_type "any" (default): contact must have ALL required tags, but may
    also carry additional tags (a superset match).
    match_type "exact": contact's tag set must be EXACTLY the required tags,
    no more and no less. Used for campaigns launched from a specific
    "Grouped by Labels" combination on the Contacts page, so the campaign
    doesn't also catch contacts that have those tags plus others.
    """
    required = normalize_tags(required_tags)
    if not required:
        return list(contacts)
    if match_type == "exact":
        return [c for c in contacts if set(get_tags(c)) == required]
    return [c for c in contacts if required.issubset(set(get_tags(c)))]
