# -*- coding: utf-8 -*-
from difflib import SequenceMatcher


def string_cleaning(text):
    text = text.replace(' ', '')
    text = text.replace(u'á', 'a')
    text = text.replace(u'é', 'e')
    text = text.replace(u'í', 'i')
    text = text.replace(u'ó', 'o')
    text = text.replace(u'ú', 'u')
    text = text.replace(u'ü', 'u')
    text = text.replace(u'ñ', 'n')
    text = text.replace(u'Á', 'A')
    text = text.replace(u'É', 'E')
    text = text.replace(u'Í', 'I')
    text = text.replace(u'Ó', 'O')
    text = text.replace(u'Ú', 'U')
    text = text.replace(u'Ü', 'U')
    text = text.replace(u'Ñ', 'n')
    return text.lower()


def find_closers(seq_list, seq_target, threshold=0.7):
    min_ratio = 0
    closer = ''

    seq_target = string_cleaning(seq_target)

    for seq in seq_list:
        ratio = SequenceMatcher(None, seq_target, string_cleaning(seq)).ratio()
        if ratio > min_ratio:
            min_ratio = ratio
            closer = seq

    return closer, min_ratio

# print find_closers(['INTERNACIONAL VARADERO'], 'Hotel Nacional de Cuba')
