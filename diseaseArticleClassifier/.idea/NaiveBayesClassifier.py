import math
import os
from os.path import join
import urllib
import string
import re
from bs4 import BeautifulSoup
from bs4 import SoupStrainer
import pickle


class NaiveBayesClassifier:

    def __init__(self, dataFile = None):
        # should be string containing the location of the training data
        self.parentURL = "/Users/jtmurphy89/PycharmProjects/diseaseArticleClassifier/trainingData/training/"
        if dataFile:
            dFile = open(dataFile, 'rb')
            self.trainingList = pickle.load(dFile)
            self.tocWords = pickle.load(dFile)
            self.tocCounts = pickle.load(dFile)
            self.tocPriors = pickle.load(dFile)
            dFile.close()
        else:
            self.trainingList = []
            self.tocWords = {}
            self.tocCounts = {
                "positive": {},
                "negative": {}
            }
            self.tocPriors = {
                "positive": 0.,
                "negative": 0.
            }
            for category in ["positive", "negative"]:
                for article in os.listdir(self.parentURL + category):
                    self.trainingList.append((category,article))
                    self.tocPriors[category] += 1
                    s = join(self.parentURL+category,article)
                    newWordCount = self.tocReader(urllib.pathname2url(s))
                    for word, count in newWordCount.items():
                        self.tocWords[word] = self.tocWords.get(word, 0.0) + count
                        self.tocCounts[category][word] = self.tocCounts[category].get(word,0.0) + count
            # dataFile = open('data.pkl','wb')
            # pickle.dump(trainingList, dataFile, -1)
            # pickle.dump(tocWords, dataFile)
            # pickle.dump(tocCounts, dataFile)
            # pickle.dump(tocPriors, dataFile)
            # dataFile.close()
        self.pPos = (self.tocPriors["positive"] / sum(self.tocPriors.values()))
        self.pNeg = (self.tocPriors["negative"] / sum(self.tocPriors.values()))


    # INPUT: string containing the url of an html wiki article
    # OUTPUT: dict of pairs (tocWord, count) where tocWord is a word in the TOC and count is the no. of times
    #         it appears in the url's TOC
    def tocReader(self, url):
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

    # INPUT: string containing the url of an html wiki article
    # OUTPUT: P(+|article), P(-|article) and whether or not the classifier thinks the article is about
    #         a disease.
    def evaluate(self,url):
        logPPos = 0.0
        logPNeg = 0.0
        testCount = self.tocReader(url)
        page = urllib.urlopen(url).read()
        soup = BeautifulSoup(page, "html.parser")
        title = soup.title.string
        title = title[0:len(title)-35]
        # in case the TOC is empty, just check for a diseases database reference...
        if not testCount:
            if not soup.find(title="Diseases Database"):
                return False, title + " is NOT a disease article..."
            else:
                return True, title + " is a disease article!"
        for w, c in testCount.items():
            if not w in self.tocWords or len(w) <= 3:
                continue
            pWord = self.tocWords[w] / sum(self.tocWords.values())
            pWordPos = self.tocCounts["positive"].get(w, 0.0) / sum(self.tocCounts["positive"].values())
            pWordNeg = self.tocCounts["negative"].get(w, 0.0) / sum(self.tocCounts["negative"].values())
            if pWordPos > 0:
                logPPos += math.log(c * pWordPos / pWord)
            if pWordNeg > 0:
                logPNeg += math.log(c * pWordNeg / pWord)
        pPosGivenArticle = math.exp(logPPos + math.log(self.pPos))
        pNegGivenArticle = math.exp(logPNeg + math.log(self.pNeg))
        #print "P(+|" + title + ") = ", pPosGivenArticle
        #print "P(-|" + title + ") = ", pNegGivenArticle
        if(pPosGivenArticle > pNegGivenArticle):
            # search for DiseasesDB reference...
            if not soup.find(title="Diseases Database"):
                return False, title + " is NOT a disease article..."
            else:
                return True, title + " is a disease article!"
        else:
            return False, title + " is NOT a disease article..."

    def smokeTest(self):
        falseNegatives = 0.
        falsePositives = 0.
        pCount = 0.
        nCount = 0.
        for article in os.listdir(self.parentURL + "positive"):
            pCount += 1
            s = join(self.parentURL+"positive",article)
            result, resultString = self.evaluate(urllib.pathname2url(s))
            if result:
                continue
            else:
                falseNegatives += 1
        pError = falseNegatives / pCount
        print "Rate of False Negatives = ", pError*100.0
        for article in os.listdir(self.parentURL + "negative"):
            nCount += 1
            s = join(self.parentURL+"negative",article)
            result, resultString = self.evaluate(urllib.pathname2url(s))
            if not result:
                continue
            else:
                falsePositives += 1
        nError = falsePositives / nCount
        print "Rate of False Positives = ", nError*100.0
        accuracy = (((nCount - falsePositives) + (pCount - falseNegatives)) / (nCount + pCount))*100.0
        print "Total Accuracy = ", accuracy
        print falseNegatives
        print pCount
        print falsePositives
        print ncount

# smoke testing
classifier = NaiveBayesClassifier(dataFile='data.pkl')
classifier.smokeTest()

# for funzies
protoUrl = "/Users/jtmurphy89/PycharmProjects/diseaseArticleClassifier/trainingData/training/"
penicillinUrl = "https://en.wikipedia.org/wiki/Penicillin"
cancerUrl = "https://en.wikipedia.org/wiki/Cancer"
penicillinBool, penicillinString = classifier.evaluate(penicillinUrl)
cancerBool, cancerString = classifier.evaluate(cancerUrl)
print penicillinString
print cancerString


