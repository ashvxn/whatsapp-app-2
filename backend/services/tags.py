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
