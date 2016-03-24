# -*- coding: utf-8 -*-
from collections import Counter
from difflib import SequenceMatcher
import operator


class CorpusDict:
    def __init__(self, item_list, aliases={}):
        self.item_list = item_list
        self.termsDict = {}  # key:term value:frequency, items
        for item in item_list:
            terms = self.get_terms(item)
            for term in terms:
                self.termsDict.setdefault(term, [0, []])
                self.termsDict[term][0] += 1
                self.termsDict[term][1].append(item)
        self.duplicates = [key for key, value in Counter(self.item_list).iteritems() if value > 1]
        self.aliases = aliases

    def update_corpus(self, item):
        terms = self.get_terms(item)
        for term in terms:
            self.termsDict.setdefault(term, [0, []])
            self.termsDict[term][0] += 1
            self.termsDict[term][1].append(item)

    def add_item(self, item):
        self.item_list.append(item)
        self.update_corpus(item)

    def get_terms(self, item_string):
        item_string = item_string.replace(u'-', ' ')
        item_string = item_string.replace(u'&', ' ')
        terms = [self.string_cleaning(i) for i in item_string.split(' ')]
        try:
            terms.remove('')
        except:
            pass
        return terms

    def get_closers(self, target_item, min_ratio=0.4, min_rratio=0.7):
        if target_item in self.aliases.keys():
            target_item = self.aliases[target_item]
        return self.get_item_closers(target_item)

    def get_item_closers(self, target_item, min_ratio=0.4, min_rratio=0.7):
        terms = self.get_terms(target_item)
        asociated_terms = {}
        candidate_items = []
        for term in terms:
            closer, ratio = self.get_closer_term(term)
            asociated_terms[closer] = ratio
            candidate_items.extend(self.termsDict[closer][1])

        candidate_items = list(set(candidate_items))
        candidates_values = {}
        for item in candidate_items:
            candidates_values[item] = self.compute_distance(asociated_terms.copy(), item)

        candidates = sorted(candidates_values.iteritems(), key=operator.itemgetter(1))
        if len(candidates) == 0 or (len(candidates) == 1 and candidates[-1][1] <= min_ratio):
            result = []
        else:
            curr_cndte = candidates.pop()
            result = [curr_cndte]
            if len(candidates) > 0:
                next_cndte = candidates.pop()
                while next_cndte[1] / curr_cndte[1] > min_rratio:
                    result.append(next_cndte)
                    curr_cndte = next_cndte
                    if len(candidates) == 0:
                        break
                    next_cndte = candidates.pop()

        # to detect cases of repeated elements in item_list
        for elem in result:
            counter = self.item_list.count(elem[0])
            idx = result.index(elem)
            result[idx] = (result[idx][0], counter, result[idx][1])
        return result

    # return sorted(candidates_values.iteritems(), key=operator.itemgetter(1))

    def compute_distance(self, asociated_terms, dictItem):
        target_terms = asociated_terms.keys()
        dict_terms = self.get_terms(dictItem)

        intersection = list(set(target_terms).intersection(dict_terms))
        union = list(set(target_terms).union(dict_terms))

        for term in dict_terms:
            if term not in asociated_terms:
                asociated_terms[term] = 1.0 / self.termsDict[term][0]

        intersum = 0
        for term in intersection:
            intersum += asociated_terms[term]

        for term in target_terms:
            asociated_terms[term] = 1.0

        unionsum = 0
        for term in union:
            unionsum += asociated_terms[term]
        if intersum / unionsum > 0.99999:
            return 1.0
        return intersum / unionsum

    def string_cleaning(self, text):
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
        text = text.replace(u'"', '')
        text = text.replace(u'-', ' ')
        text = text.replace(u'&', ' ')
        return text.lower()

    def get_closer_term(self, target_term):

        min_ratio = 0
        closer = ''

        target_term = self.string_cleaning(target_term)

        for term in self.termsDict.keys():
            ratio = SequenceMatcher(None, target_term, self.string_cleaning(term)).ratio()
            if ratio > min_ratio:
                min_ratio = ratio
                closer = term

        return closer, min_ratio
