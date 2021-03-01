#libraries for core functionality
import pandas as pd
import epo_ops
from bs4 import BeautifulSoup
import sys

#libraries for handling errors and special cases
import re
import numpy as np

print("\nBEGINNING OF SCRIPT\n")

#FUNCTION: convert list of filing names to query
def generateQuery(instName):
'''
generateQuery:
Argument (string): Set of institution names separated by commas
    - May not include the "/" character*
    - Should not be just " "**
Returns (string): A string

*Search interprets the "/" character as webpage jargon and it destroys the search.
	We've tried replacing "/" with: %2F, \/, and \\
	Replacing "/" with " " in input document appears to leave results unchanged?
**Further development: Interpret " " as NaN
	Forbidding " " entries in input document is effective

'''
	split_name = re.split(',',instName) #splits multiple institutions into list
	if len(split_name) == 1: #just one name - add search logic bookends
		epoQuery = 'pa="' + split_name[0] + '"' 
	else: #more than one name - include OR between terms
		epoQuery = 'pa="' + split_name[0] + '"'
		for i in range(1, len(split_name)):
			epoQuery = epoQuery + ' OR pa="' + split_name[i] + '"'
	
	return epoQuery

#FUNCTION: retrieve number of results and object size for given institution
def getCount(searchQuery):
'''
getCount:
Argument (string): A search query already in EPO format
    - Should be output from generateQuery
Returns count (int or NaN): Number of patent records matching query*
Returns size (int): Size in bytes of data retrieved through API
    - API is free for less than 4 GB per week, so best to keep track

*Each search query cannot render more than 10,000 results, so to read through all patents 
    in results the search must run x/10,000 many times where x is total number of results.
	We cannot guess x/10,000 because overshooting (i.e. range_end=x+1) will cause an error
	and undershooting will exclude some results. 
 To improve this: Include additional filter criteria in the query to split results (e.g.
    break up before and after specific years) and add up count of both/all pieces.
'''
	
	print(searchQuery)
	try:
		response = client.published_data_search(cql=searchQuery, 
			range_begin=1, 
			range_end=1, 
			constituents=None) #run search for institution
		soup = BeautifulSoup(response.text, 'xml')
		searchSummary = soup('ops:biblio-search')
		count = int(searchSummary[0]['total-result-count']) #grab count as int
		size = sys.getsizeof(response) #grab size
	except:
		print('\tThis search query could not be processed.')
		count = np.nan
		size = 0
	
	return count, size #return patent count and response size

#user selects set of institutions to process
country = input("Country to process: ")
sheet = input("Sheet to process: ")

#read in set of institutions
inputFile = str(country) + '.xlsx'
institutions = pd.ExcelFile(inputFile)
institSheet = institutions.parse(sheet)
filingNames = list(institSheet['PatentFilingName'].dropna().values)

#Df for storing count values
countDf = pd.DataFrame(index=filingNames, columns=['CountPatents'])

#global variables for managing API
client = epo_ops.Client(key='get your own key', secret='also yours') #instantiate client
dataUse = 0 #total of data (in bytes) downloaded from OPS

print('\nQueries running through search:')
for instit in filingNames: #Going through institutions one by one
	query = generateQuery(instit) #Generate search query
	count, size = getCount(query) #Pull number of patents on EPO database for institutions
	countDf.loc[instit] = count #Store value
	dataUse = dataUse + size #Add size of returned object to total volume of data closed

#Display aggregate size of data called
print("Data volume called from OPS in this run: " + str(dataUse) + " bytes")

#Export df
exportName = country + "-" + sheet + "-patentCount.csv"
countDf.to_csv(exportName, encoding='utf-8-sig')

print("\nCOMPLETE - Check current directory for results file.\n")