import math
import os
from os.path import join
import urllib
import string
import re
from bs4 import BeautifulSoup
from bs4 import SoupStrainer
import pickle

dataFile = open('data.pkl', 'rb')
trainingList = pickle.load(dataFile)
tocWords = pickle.load(dataFile)
tocCounts = pickle.load(dataFile)
tocPriors = pickle.load(dataFile)
dataFile.close()

pPos = (tocPriors["positive"] / sum(tocPriors.values()))
pNeg = (tocPriors["negative"] / sum(tocPriors.values()))
parentURL = "/Users/jtmurphy89/PycharmProjects/diseaseArticleClassifier/trainingData/training/"

def tocReader(url):
        page = urllib.urlopen(url).read()
        product = SoupStrainer('div',{'id': 'toc'})
        soup = BeautifulSoup(page, "html.parser", parse_only=product)
        excluded = ['external', 'links', 'references', 'bibliography']
        wordCount = {}
        for titleName in soup.find_all('a'):
            #nohashtags
            s = str(titleName['href'][1:])
            s = s.translate(string.maketrans("_", " ")).lower()
            s = s.translate(string.maketrans("",""), string.punctuation)
            wordList = re.split("\W+", s)
            trimmedList = [aa for aa in wordList if aa not in excluded]
            if not trimmedList:
                continue
            else:
                for word in trimmedList:
                    wordCount[word]= wordCount.get(word,0.0) + 1.0
        return wordCount







# smoke test
logPPos = 0.0
logPNeg = 0.0
#testCount = tocReader(join(parentURL+"positive", "Aagenaes_syndrome"))
testCount = tocReader("https://en.wikipedia.org/wiki/Penicillin")
# if not testCount:
#     page = urllib.urlopen(join(parentURL+"positive", "Aagenaes_syndrome")).read()
#     soup = BeautifulSoup(page, "html.parser")
#     if not soup.find(title="Diseases Database"):
#         print "Article is NOT a disease article..."
#     else:
#         print soup.title.string
for w, c in testCount.items():
    if not w in tocWords or len(w) <= 3:
        continue
    p_word = tocWords[w] / sum(tocWords.values())
    p_w_given_pos = tocCounts["positive"].get(w, 0.0) / sum(tocCounts["positive"].values())
    p_w_given_neg = tocCounts["negative"].get(w, 0.0) / sum(tocCounts["negative"].values())
    if p_w_given_pos > 0:
        logPPos += math.log(c * p_w_given_pos / p_word)
    if p_w_given_neg > 0:
        logPNeg += math.log(c * p_w_given_neg / p_word)

probPlus = math.exp(logPPos + math.log(pPos))
probMinus = math.exp(logPNeg + math.log(pNeg))
print "Score(pos): ", probPlus
print "Score(neg): ", probMinus
if(probPlus > probMinus):
    # search for DiseasesDB reference as it could be a fluke...
    page = urllib.urlopen("https://en.wikipedia.org/wiki/Penicillin").read()
    soup = BeautifulSoup(page, "html.parser")
    if not soup.find(title="Diseases Database"):
        print "Article is NOT a disease article..."
    else:
        print soup.title.string