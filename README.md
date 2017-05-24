# case-reports

This repository contains a collection of functions in Python 2.7 to assist with PubMed queries.

In order to generate a citation count distribution, use the function ```buildDistribution()``` (line 125 - 150) in the file ```citation_distrib.py```.

Input:
First, define the publication set from which you wish to generate the distribution. You must specify a list of MeSH terms (e.g., Cardiovascular Disease) that are required for a publication to be included in the set. For a publication to be counted it requires only one of the specified MeSH terms.

Optionally, you may specify a list of PMIDs that will be excluded from the set, as well as a range of publication dates (line 129). You may also specify whether you wish to search MeSH Terms or MeSH Major Topics.

If you wish to search MeSH Major Topics (line 16), then set the variable to TRUE. All other parameters can be set on line 129.

Output:
The output is a map in which each key is the number of citations for a given publication in PubMed Central (PMC), and each value is the number of publications in the queried set with that citation total. For example, the distribution

```
{'0': 23, '1': 3, '4': 2}
```

would describe a set of 28 publications, 23 of which had no citations in PMC, 3 of which had 1 publication in PMC, and 2 of which had 4 publications in PMC.

These counts represent minimum citation counts. Notably, a publication could be cited by other publications which are not tracked in PMC.
