import os, re
from nltk.stem.snowball import SnowballStemmer
from nltk.corpus import stopwords
from HTMLParser import HTMLParser
from qdr import Trainer, QueryDocumentRelevance
import pandas as pd

def removeCharacter(word):
    cleaned_word = ''
    unwanted_ch = ["'", '"', '|']
    for l in word:
        if not l in unwanted_ch:
           cleaned_word += l
    return cleaned_word

def removePunctuation(word):
    # remove quotes
    word = removeCharacter(word)
    if len(word):
        if word[-1] in '!*+,-.:;?_':
            return word[:-1]
    return word

def buildCorpus():
    # init result lists
    corpus = list()
    bug_ids = list()
    # init model obj
    stemmer = SnowballStemmer('english')
    stop_words = set(stopwords.words('english'))
    h = HTMLParser()
    # build corpus from bug reports
    current_dir = os.getcwd()
    bug_reports = os.listdir('analyzed_bugs')
    os.chdir('analyzed_bugs')
    for br in bug_reports:
        with open(br) as f:
            reader = f.read()
            raw_title = re.findall(r'\<short_desc\>(.+?)\<\/short_desc\>', reader)[0]
            stemmed_title = list()
            for word in raw_title.split(' '):
                if len(word):
                    word = h.unescape(word)
                    word = removePunctuation(word)
                    stemmed_word = stemmer.stem(word)
                    if (stemmed_word not in stop_words) and (len(stemmed_word) > 0):
                        stemmed_title.append(stemmed_word)
            corpus.append(stemmed_title)
            bug_ids.append(br[:-4])
    os.chdir(current_dir)
    return corpus, bug_ids

if __name__ == "__main__":
    corpus, bug_ids = buildCorpus()

    model = Trainer()
    model.train(corpus)
    model.serialize_to_file('trained_model.gz')

    scorer = QueryDocumentRelevance.load_from_file('trained_model.gz')
    result_list = list()
    for i in range(len(corpus)-1):
        for j in range(i+1, len(corpus)):
            #print i, j
            relevance_scores = scorer.score(corpus[i], corpus[j])
            if relevance_scores['bm25'] > 0:
#                print bug_ids[i], bug_ids[j], '%.2f' %relevance_scores['bm25']
                result_list.append([bug_ids[i], bug_ids[j], relevance_scores['bm25']])
    
    df = pd.DataFrame(result_list, columns=['bug1', 'bug2', 'bm25'])
    sorted_df = df.sort_values(by='bm25', ascending=False)
    print sorted_df
    sorted_df.to_csv('title_relevance.csv', index=False)



