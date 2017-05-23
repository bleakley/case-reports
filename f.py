import json, re, requests

data = {}
with open("/home/bleakley/funding_source.json",) as data_file:
    data = json.load(data_file)

docs = data["response"]["docs"]

for prefix in ['OD','CA','EY','HL','HG','AG','AA','AI','AR','EB','HD','DC','DE','DK','DA','ES','GM','MH','MD','NS','NR','LM','CL','CT','RG','TW','TR','AT']:

    all_grants ={}

    count = 0
    for tool in docs:
        tool_grants = {}

        count += 1
        if count % 50 == 0:
            print count

        doi = tool["publicationDOI"]
        query = 'http://api.crossref.org/works/' + doi
        response = requests.get(query).content
        try:
            year = json.loads(response)["message"]["indexed"]["date-parts"][0]
        except:
            print response
            continue
        if year < 2014:
            print "year" + str(year)
            continue

        for fs in tool["funding"]:
            m = re.search(prefix + '\d\d\d\d\d\d', fs)
            if m:
                tool_grants[m.group(0)] = True

        for g in tool_grants.keys():
            if g in all_grants:
                all_grants[g] += 1
            else:
                all_grants[g] = 1

    print prefix + " " + str(sum(all_grants.values()))
