from xml.etree.ElementTree import fromstring

import operator
import requests, json, io, xmljson, HTMLParser, time

working_dir='/home/bleakley/case-reports/'

# MeSH Term lists
ihd = ['Myocardial Ischemia', 'Myocardial Stunning']
cva = ['Cerebrovascular Disorders']
cardiomyopathy = ['Cardiomegaly','Cardiomyopathies','Endocarditis','Heart Failure','Ventricular Dysfunction','Ventricular Outflow Obstruction']
arrhythmia = ['Arrhythmias, Cardiac', 'Heart Arrest']
valvedisease = ['Heart Valve Diseases','Rheumatic Heart Disease']
chd = ['Cardiovascular Abnormalities','Heart Defects, Congenital']

majorTopics = True

# Get a list of PMIDs match a set of MeSH terms, excluded MeSH terms, and optional dates
def getPmids(meshTerms, maxCount, excluded={}, startDate=1900, endDate=3000):
    termString = ""
    for i, term in enumerate(meshTerms):
        if majorTopics:
            termString += '("' + term + '"[MeSH Major Topic])'
        else:
            termString += '("' + term + '"[MeSH Terms])'
        if i != len(meshTerms) - 1 :
            termString += ' OR '

    step = 100000
    trueCount = 99999999
    startCount = 0
    list = []
    while startCount < trueCount:
        query = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=("case reports"[Publication Type]) AND (' + termString + ') AND("' + str(startDate) +  '"[Date - Publication] : "' + str(endDate) + '"[Date - Publication]) AND ("english"[Language])&retmode=json&retmax=' + str(step) + '&retstart=' + str(startCount)
        print query
        d = json.loads(requests.get(query).content)["esearchresult"]
        trueCount = int(d["count"])
        list += d["idlist"]
        startCount += step

    newlist = []
    for x in list:
        if x not in excluded:
            newlist.append(x)
    return newlist[0:maxCount]

def getAuthorString(authors):
    authorString = ""
    for author in authors:
        authorString += author["name"] + ", "
    authorString = authorString[:-2]
    return authorString

refCounts = {}

def getTableRow(jsonData):
    row = ""
    row += getAuthorString(jsonData["authors"])
    row += '\t'
    row += jsonData["title"]
    row += '\t'
    row += jsonData["source"]
    row += '\t'

    doi = "None"
    pmid = "None"
    otherIds = jsonData["articleids"]
    for otherId in otherIds:
        if otherId["idtype"] == "doi":
            doi = otherId["value"]
        if otherId["idtype"] == "pubmed":
            pmid = otherId["value"]
    row += doi
    row += '\t'
    row += pmid
    row += '\t'
    year = jsonData["pubdate"].split()[0]
    row += year
    row += '\t'
    link = 'https://www.ncbi.nlm.nih.gov/pubmed/' + pmid
    if doi != "None":
        link = 'https://dx.doi.org/' + doi
    row += link
    refCount = str(jsonData["pmcrefcount"])
    if refCount == "":
        refCount = "0"
    if refCount in refCounts:
        refCounts[refCount] += 1
    else:
        refCounts[refCount] = 1
    row += '\t'
    row += refCount
    return row

def countRowRef(jsonData):
    try:
        refCount = str(jsonData["pmcrefcount"])
        if refCount == "":
            refCount = "0"
        if refCount in refCounts:
            refCounts[refCount] += 1
        else:
            refCounts[refCount] = 1
    except:
        print "row failed"


def getTableRows(pmids):
    query = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&rettype=abstract&id='
    for pmid in pmids:
        query += pmid + '+'
    query = query[:-1]
    try:
        result = json.loads(requests.get(query).content)["result"]
    except:
        print "request failed"
        print query
        return
    rows = ""
    for uid in result["uids"]:
        countRowRef(result[uid])
    return rows


def buildDistribution():
    excluded = {}
    file = io.open(working_dir + 'dump', 'w', encoding='utf8')
    print "Getting list of PMIDs..."
    pmids = getPmids(['Cardiovascular Diseases'], 1000000, excluded, 1950, 2015)
    print "Total found " + str(len(pmids))
    print "Downloading data..."
    step = 500
    lastPercent = 0
    last_time = time.time()
    for i in range(0,len(pmids),step):
        rows = getTableRows(pmids[i:min(i+step,len(pmids)-1)])
        newPercent = int(100.0*i/len(pmids))
        if newPercent != lastPercent:
            delta_time = time.time() - last_time
            last_time = time.time()
            eta = delta_time*(100 - newPercent)/60.0
            hours = int(eta/60.0)
            print str(newPercent) + "% " + str(hours) + " hours, " + str(int(eta-60*hours)) + " minutes remaining"
        lastPercent = newPercent
    file.close()
    counts = refCounts.keys()
    for c in counts:
        print c + "\t" + str(refCounts[c])
    print refCounts
    print "Done."

buildDistribution()
