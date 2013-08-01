import string
import simplejson
import requests
import nltk
import random

#We want to eliminate all punctuation except single quotes.
#This isn't the only case (sometimes you have single quotes around a word, which we do want to get rid of)
#TODO: a regex that will do this better than the current method (python's string.punctuation without the single quote)
#TODO: find a list of stopwords, don't count them
#nltk?


def common_words(text, max_items=15):
    # TODO: make stopword language configurable?
    stopwords = nltk.corpus.stopwords.words('english')

    tokens = nltk.word_tokenize(text)

    words = [w.lower() for w in tokens
             if w.isalnum() and w.lower() not in stopwords]
    # NOTE: isalnum will restrict to alpha and numeric content (i.e., words & dates);
    # will probalby drop date ranges as well as contractions or quoted terms

    freqdist = nltk.FreqDist()
    for word in words:
        freqdist.inc(word)

    if max_items is None:
        return {'keywords': freqdist.keys()}
    return {'keywords': freqdist.keys()[:max_items]}

    # TODO: also look at using nltk to generate collocations


"""
Returns JSON response from dbpedia spotlight annotate (or other source)
"""
def query(query) :
    r = requests.get(query['url'], params=query['params'], headers = {'accept': 'application/json'})

    return r.text

"""
Return a set named entities from a Spotting query
"""
def get_names_from_spotting(doc) :
    json_data = simplejson.loads(doc)
    stopwords = nltk.corpus.stopwords.words('english')

    name_set = set()
    for item in json_data['annotation']['surfaceForm'] :
        name = str(item['@name'])
        name = name.translate(None, string.punctuation).strip()
        if(name not in stopwords) :
            name_set.add(name.lower())
    return name_set

"""
"""
def get_names_from_annotate(doc) :
    json_data = simplejson.loads(doc)
    name_set = set()

    for item in json_data['Resources'] :
        name_set.add(item['@surfaceForm'].lower())

    return name_set

"""
Returns a dictionary of search terms
keywords - combination of spotting and annotate queries 
people - 
places - 
"""
def get_search_terms(text) :
    spot = {
        'url':'http://spotlight.dbpedia.org/rest/spot',
        'params': {
            'text':text,
        }
    }

    annotate = {
        'url': 'http://spotlight.dbpedia.org/rest/annotate',
        'params': {
            'text': text,
            'confidence': 0.3,
            'support': 60,
        }
    }

    terms = { }

    spot_set = set()
    annotate_set = set()

    resp_s = query(spot)
    spot_set = get_names_from_spotting(resp_s)

    resp_a = query(annotate)
    annotate_set = get_names_from_annotate(resp_a)

    terms = _get_types(resp_a)
    # get a random set of keywords from the union of spot and annotate
    terms['keywords'] = _get_random(spot_set.union(annotate_set))
    # todo -- Randomize or mix up the set of keywords being passed
    return terms

# Gets a random set of (at most 15) keywords
def _get_random(keywords, max_items=15) :
    if(max_items > len(keywords)) :
        max_items = len(keywords)/2
    return random.sample(keywords, max_items)


def _get_types(entities) :
    json_data = simplejson.loads ( entities )
    types = {
        'people': [],
        'places': [],
    }
    for item in json_data['Resources'] :
        str_types = str(item['@types'])
        if('DBpedia:Person' in str_types) :
            types['people'].append(item['@surfaceForm'])
        if('DBpedia:Place' in str_types) :
            types['places'].append(item['@surfaceForm'])
    return types
