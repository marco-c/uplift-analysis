import get_bugs
import os, re, csv, subprocess
from nltk.stem.snowball import SnowballStemmer
from nltk.corpus import stopwords
from HTMLParser import HTMLParser
from qdr import Trainer, QueryDocumentRelevance
import pandas as pd

# Run shell command from a string
def shellCommand(command_str):
    cmd =subprocess.Popen(command_str.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    cmd_out, cmd_err = cmd.communicate()
    return cmd_out

def removeCharacter(word):
    cleaned_word = ''
    unwanted_ch = ["'", '"', '|']
    for l in word:
        if not l in unwanted_ch:
           cleaned_word += l
    cleaned_word.replace('\n', ' ')
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
    corpus = dict()
    # init model obj
    stemmer = SnowballStemmer('english')
    stop_words = set(stopwords.words('english'))
    h = HTMLParser()
    # build corpus from bug reports
    all_bugs = get_bugs.get_all()
    for bug_item in all_bugs:
        raw_title = bug_item['summary']
        stemmed_title = list()
        for word in raw_title.split(' '):
            if len(word):
                word = h.unescape(word)
                word = removePunctuation(word)
                stemmed_word = stemmer.stem(word)
                if (stemmed_word not in stop_words) and (len(stemmed_word) > 0):
                    stemmed_title.append(stemmed_word.encode('utf8'))
        corpus[bug_item['id']] = stemmed_title        
    return corpus

def loadBugIDs(filename, uplift_bugs):
    with open('independent_metrics/' + filename) as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            uplift_bugs.add(int(row[0]))
    return uplift_bugs

if __name__ == "__main__":
    print 'Building corpus ...'
    corpus = buildCorpus()
    print 'Loading uplift bugs ...'
    uplift_bugs = set()
    uplift_bugs = loadBugIDs('basic_aurora.csv', uplift_bugs)
    uplift_bugs = loadBugIDs('basic_beta.csv', uplift_bugs)
    uplift_bugs = loadBugIDs('basic_release.csv', uplift_bugs)
    print 'Training model ...'
    model = Trainer()
    model.train(corpus.values())
    model.serialize_to_file('trained_model.gz')
    scorer = QueryDocumentRelevance.load_from_file('trained_model.gz')
    result_list = list()
    analyzed_pairs = set()
    for all_id in corpus:
        for uplift_id in uplift_bugs:
            if not (all_id == uplift_id):
                id_pair = sorted([all_id, uplift_id])
                pair_str = '%d^%d' %(id_pair[0],id_pair[1])
                if not pair_str in analyzed_pairs:
                    analyzed_pairs.add(pair_str)
                    relevance_scores = scorer.score(corpus[id_pair[0]], corpus[id_pair[1]])
                    if relevance_scores['bm25'] > 0:
    #                    print bug_ids[i], bug_ids[j], '%.2f' %relevance_scores['bm25']
                        result_list.append([corpus[id_pair[0]], corpus[id_pair[1]], relevance_scores['bm25']])
    shellCommand('sudo sysctl -w vm.drop_caches=3')
    print 'Outputing results ...'
    df = pd.DataFrame(result_list, columns=['bug1', 'bug2', 'bm25'])
    sorted_df = df.sort_values(by='bm25', ascending=False).round({bm25:2})
#    print sorted_df
    sorted_df.to_csv('title_relevance.csv', index=False)
