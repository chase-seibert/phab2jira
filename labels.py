from slugify import slugify

import settings


def generate_labels(string_values):
    # sorted == the order then come back in from the API, for compare
    return tuple(sorted(set([slugify(tag) for tag in string_values])))


def one_label_in_set(labels, label_set):
    for label in labels:
        if label in label_set:
            return True
    return False
