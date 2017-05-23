from xml.etree.ElementTree import fromstring

import operator
import requests, json, io, xmljson, HTMLParser, time

#Author Name	Title	Journal	DOI	PMID	Year	Link to Full Text

def getPmids(meshTerms, maxCount, excluded={}, startDate=1900, endDate=3000):
    # http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=("case reports"[Publication Type]) AND ("Heart Valve Diseases"[MeSH Terms]) &retmode=json&retmax=1000
    termString = ""
    for i, term in enumerate(meshTerms):
        #termString += '("' + term + '"[MeSH Terms])'
        termString += '("' + term + '"[MeSH Major Topic])'
        if i != len(meshTerms) - 1 :
            termString += ' OR '

    maxCount = maxCount + len(excluded) #what is the point of this line?

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

    #query = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=("case reports"[Publication Type]) AND (' + termString + ') AND ("english"[Language])&retmode=json&retmax=' + str(maxCount)
    #query = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=("case reports"[Publication Type]) AND ("english"[Language])&retmode=json&retmax=' + str(maxCount)
    #print query

    #list = json.loads(requests.get(query).content)["esearchresult"]["idlist"]
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
    #https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&rettype=abstract&id=4758320+4756262
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
        #row = getTableRow(result[uid])
        #rows += row + '\n'
    return rows

def buildTable():
    ihd = ['Myocardial Ischemia', 'Myocardial Stunning']
    cva = ['Cerebrovascular Disorders']
    cardiomyopathy = ['Cardiomegaly','Cardiomyopathies','Endocarditis','Heart Failure','Ventricular Dysfunction','Ventricular Outflow Obstruction']
    arrhythmia = ['Arrhythmias, Cardiac', 'Heart Arrest']
    valvedisease = ['Heart Valve Diseases','Rheumatic Heart Disease']
    chd = ['Cardiovascular Abnormalities','Heart Defects, Congenital']

    excluded = {}
    #for x in [ihd, cva, cardiomyopathy, arrhythmia, valvedisease, chd]:
    #    for i in getPmids(x, 1000000):
    #        excluded[i] = True

    file = io.open('/home/bleakley/case_reports/dump', 'w', encoding='utf8')
    #file = open('/home/bleakley/case_reports/dump','w')
    print "Getting list of PMIDs..."
    pmids = getPmids(['Cardiovascular Diseases'], 1000000, excluded, 1970)
    #pmids = getPmids(['*'], 5000000, {})
    #Neoplasms
    #Digestive System Diseases
    #Respiratory Tract Diseases
    #Nervous System Diseases
    #pmids = getPmids(chd, 1000000, {})
    print "Total found " + str(len(pmids))
    print "Downloading data..."
    step = 500
    lastPercent = 0
    last_time = time.time()
    for i in range(0,len(pmids),step):
        rows = getTableRows(pmids[i:min(i+step,len(pmids)-1)])
        #file.write(rows)
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

#buildTable()

def countReferences():
    file = io.open('/home/bleakley/case_reports/all_case_reports', 'r', encoding='utf8')

    with open('/home/bleakley/case_reports/all_case_reports') as f:
        content = f.readlines()
        content = [x.strip() for x in content]

        #pmids = content[0:500000]
        #pmids = content[500001:900000]
        pmids = content[900001:]

        print "Total found " + str(len(pmids))
        print "Downloading data..."
        step = 500
        lastPercent = 0
        last_time = time.time()
        for i in range(0, len(pmids), step):
            rows = getTableRows(pmids[i:min(i + step, len(pmids) - 1)])
            # file.write(rows)
            newPercent = int(100.0 * i / len(pmids))
            if newPercent != lastPercent:
                delta_time = time.time() - last_time
                last_time = time.time()
                eta = delta_time * (100 - newPercent) / 60.0
                hours = int(eta / 60.0)
                print str(newPercent) + "% " + str(hours) + " hours, " + str(int(eta - 60 * hours)) + " minutes remaining"
            lastPercent = newPercent
        file.close()
        counts = refCounts.keys()
        for c in counts:
            print c + "\t" + str(refCounts[c])
        print refCounts
        print "Done."

#countReferences()

def getMeshTerms(pmid):
    query = 'https://www.ncbi.nlm.nih.gov/pubmed/' + pmid + '?report=xml&format=text'
    response = requests.get(query)
    body = response.content.decode('utf-8')

    html_parser = HTMLParser.HTMLParser()
    unescaped = html_parser.unescape(body)
    #print unescaped

    return parseForMeshTerms(unescaped)

def getMeshTermsFromFile(pmid):
    temp = io.open("/home/bleakley/case_reports/after/" + str(pmid).strip() + ".xml", "r", -1, "utf-8")
    data = temp.read()
    temp.close()
    return parseForMeshTerms(data)

def parseForMeshTerms(unescaped):
    xml = fromstring(unescaped.encode('utf-8'))
    try:
        meshTerms = xmljson.badgerfish.data(xml)["pre"]["PubmedArticle"]["MedlineCitation"]["MeshHeadingList"]["MeshHeading"]

        generalData = xmljson.parker.data(xml)
        #print json.dumps(meshTerms)

        majorMeshTopics = []
        minorMeshTopics = []
        anyMeshTopics = []

        for term in meshTerms:
            #print json.dumps(term)
            t = {"ui": term["DescriptorName"]["@UI"], "name": term["DescriptorName"]["$"]}
            t2 = {"ui": term["DescriptorName"]["@UI"], "name": term["DescriptorName"]["$"] + "/ANY"}

            anyString = term["DescriptorName"]["$"] + "/ANY"
            if anyString not in anyMeshTopics:
                anyMeshTopics.append(anyString)

            mt = term["DescriptorName"]["@MajorTopicYN"] == "Y"
            if "QualifierName" in term:
                if type(term["QualifierName"]) is list:
                    for name in term["QualifierName"]:

                        n = t["name"] + "/" + name["$"]

                        q = {"ui": name["@UI"], "name": n}
                        if name["@MajorTopicYN"] == "Y":
                            majorMeshTopics.append(q)
                        else:
                            minorMeshTopics.append(q)
                else:
                    t["name"] += "/" + term["QualifierName"]["$"]
                    if term["QualifierName"]["@MajorTopicYN"] == "Y":
                        mt = True

            if mt:
                majorMeshTopics.append(t)
            else:
                minorMeshTopics.append(t)
        terms = {"majorMeshTopics": majorMeshTopics, "minorMeshTopics": minorMeshTopics, "anyMeshTopics": anyMeshTopics}

    except:
        return {"majorMeshTopics": [], "minorMeshTopics": [], "anyMeshTopics": []}

    return terms

def writeFile():
    pmids = open("/home/bleakley/case_reports/all_pmids","r")
    meshDump = open("/home/bleakley/case_reports/all_mesh","w")

    meshTermsToSave = {"majorMeshTopics": {}, "minorMeshTopics": {}, "anyMeshTopics": {}}
    lastPercent = 0
    last_time = time.time()
    i = 0
    num_lines = 241924
    for pmid in pmids:
        newPercent = int(100.0 * i / num_lines)
        i+=1
        if newPercent != lastPercent:
            delta_time = time.time() - last_time
            last_time = time.time()
            eta = delta_time * (100 - newPercent) / 60.0
            hours = int(eta / 60.0)
            print str(newPercent) + "% " + str(hours) + " hours, " + str(int(eta - 60 * hours)) + " minutes remaining"
        lastPercent = newPercent
        terms = []
        #print pmid
        try:
            terms = getMeshTermsFromFile(pmid)
        except:
            terms = getMeshTerms(pmid)
        for term in terms["majorMeshTopics"]:
            if term["name"] in meshTermsToSave["majorMeshTopics"]:
                meshTermsToSave["majorMeshTopics"][term["name"]] += 1
            else:
                meshTermsToSave["majorMeshTopics"][term["name"]] = 1
        for term in terms["minorMeshTopics"]:
            if term["name"] in meshTermsToSave["minorMeshTopics"]:
                meshTermsToSave["minorMeshTopics"][term["name"]] += 1
            else:
                meshTermsToSave["minorMeshTopics"][term["name"]] = 1
        for term in terms["anyMeshTopics"]:
            if term in meshTermsToSave["anyMeshTopics"]:
                meshTermsToSave["anyMeshTopics"][term] += 1
            else:
                meshTermsToSave["anyMeshTopics"][term] = 1

    meshDump.write(json.dumps(meshTermsToSave))
    meshDump.close()

#writeFile()

temp = io.open("/home/bleakley/case_reports/all_mesh", "r", -1, "utf-8")
mesh = temp.read()
mesh = json.loads(mesh)
temp.close()
#mesh = json.load("/home/bleakley/case_reports/all_mesh")
dump = open("/home/bleakley/case_reports/dump","w")
for term in mesh["minorMeshTopics"].keys():
    dump.write(term + "\t" + str(mesh["minorMeshTopics"][term]) + "\n")
dump.close()

#pmidDump = open("/home/bleakley/case_reports/all_pmids","w")
#pmids = getPmids(['Cardiovascular Diseases'], 10000000, {})
#for p in pmids:
#    pmidDump.write(p + "\n")
#pmidDump.close()

def before():
    pmidDump = open("/home/bleakley/case_reports/all_pmids","r")
    for line in pmidDump:
        l = line.strip()
        print l
        temp = open("/home/bleakley/case_reports/before/" + l,"w")
        temp.write("")
        temp.close()
    pmidDump.close()


import os

def after():
    while True:
        f = os.listdir("/home/bleakley/case_reports/before/")[0]
        query = 'https://www.ncbi.nlm.nih.gov/pubmed/' + f + '?report=xml&format=text'
        response = requests.get(query)
        body = response.content.decode('utf-8')

        html_parser = HTMLParser.HTMLParser()
        unescaped = html_parser.unescape(body)
        temp = io.open("/home/bleakley/case_reports/after/" + f + ".xml", "w", -1, "utf-8")
        temp.write(unescaped)
        temp.close()
        os.remove("/home/bleakley/case_reports/before/" + f)
        print f

#before()
#after()
'''categories = ['arrhythmias_mesh','cardiomyopathy_mesh','chd_mesh','cva_mesh','ihd_mesh','valve_disease_mesh']

cat_data = []
for category in categories:
    with open('/home/bleakley/case_reports/' + category) as data_file:
        try:
            cat_data.append({"name":category, "data":json.load(data_file)})
        except:
            print category

#print json.dumps(cat_data)

terms = {}'''


'''for cat in cat_data:
    ts = cat["data"]["minorMeshTopics"]
    for t in ts.keys():
        if t in terms:
            terms[t][cat["name"]] = ts[t]
            terms[t]["count"] += ts[t]
            terms[t]["categories"] += 1
        else:
            terms[t] = {cat["name"]: ts[t], "count": ts[t], "categories": 1}'''
'''
for cat in cat_data:
    print cat
#sorted_terms = sorted(terms, key=operator.attrgetter('count'), reverse=True)
#items = sorted(terms.iteritems(), key=lambda x: x['count'], reverse=True)
#print json.dumps(terms)

#for term in terms.keys():
#    print term + '\t' + str(terms[term]["count"]) + '\t' + str(terms[term]["categories"])
'''
'''
newborn		63
infant		54
preschool	44
child		64
adolescent	56
young adult	58
adult		353
aged		379
aged, 80+	127
'''

'''import math

for term in terms:
    score = 0.0
    for key in terms[term].keys():
        if key != "count" and key != "categories":
            score += math.sqrt(terms[term][key])/(terms[term]["categories"]**2)
            #score += math.sqrt(terms[term][key])
    terms[term]["score"] = score'''

#print json.dumps(terms, indent=4)

#for term in terms.keys():
#    print term + '\t' + str(terms[term]["count"]) + '\t' + str(terms[term]["categories"]) + '\t' + str(terms[term]["score"])

'''major_mesh = {}
for category in categories:
    with open('/home/bleakley/case_reports/' + category) as data_file:
        data = json.load(data_file)
    major = data["majorMeshTopics"]
    #major = sorted(major, key=major.get, reverse=True)
    for mesh in major:
        if mesh in major_mesh:
            major_mesh[mesh] += 1
        else:
            major_mesh[mesh] = 1

major_mesh = sorted(major_mesh, key=major_mesh.get, reverse=True)
print json.dumps(major_mesh)'''

def junk():
    with open('/home/bleakley/case_reports/arrhythmias_mesh') as data_file:
        data = json.load(data_file)

    #print json.dumps(data)
    major = data["majorMeshTopics"]
    major = sorted(major, key=major.get, reverse=True)
    for mesh in major:
        print mesh + "   " + str(data["majorMeshTopics"][mesh])


#for pmid in pmids:
#    terms = getMeshTerms(pmid)
#    for term in terms:
#        if term in termCounter:
#            termCounter[term] += 1
#        else:
#            termCounter[term] = 1

#print json.dumps(termCounter)
