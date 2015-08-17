__author__ = 'JMilner'

import requests
import time
import csv
import math
import os
import HTMLParser

class APIException(Exception):
    pass

def checkStackExchange(csvName, fields, startDate, endDate, locs, site, keyword):

    parser = HTMLParser.HTMLParser()
    baseSearchUrl = "http://api.stackexchange.com/2.2/search/advanced"
    baseUserUrl = "http://api.stackexchange.com/2.2/users/"

    humanStartDate = time.strftime("%d/%m/%y", time.localtime(float(startDate)))
    humanEndDate = time.strftime("%d/%m/%y", time.localtime(float(endDate)))
    print humanStartDate, "- Unix Time(", startDate, ")"
    print humanEndDate, " - Unix Time(", endDate, ")"

    searchPayload = {
        'pagesize' : 100,
        'page' : 1,
        'todate' : endDate,
        'order' : "desc",
        'sort' : "activity",
        'site' : site
    }

    userPayload = {
        'pagesize' : 100,
        'page' : 1,
        'order' : 'desc',
        'sort' : 'name',
        'site' : site
    }

    # Unique question IDS list
    question_ids = []
    output = []

    for field in fields:

        # RESET VARIABLES
        previousField = None
        questions = []
        userIds = []
        searchPayload['page'] = 1
        userPayload['page'] = 1

        # Assign file name
        outputPath = r'output'
        if not os.path.exists(outputPath): os.makedirs(outputPath)
        csvFile = outputPath + "/" + csvName + "_" + site + '.csv'

        # Perform Question Search
        print "Searching the ", site, " site for questions with", keyword, "in the ", field, "field \n"
        moreQuestions = True
        searchPayload[field] = keyword
        if previousField:
            del searchPayload[previousField]

       # print "Search payload: ", searchPayload
        while moreQuestions:
            response = requests.get(baseSearchUrl, params=searchPayload)
            print "QUESTION REQUEST URL: ", response.url
            jsonResponse = response.json()

            if "error_id" not in jsonResponse and 'has_more' in jsonResponse:
                moreQuestions = jsonResponse['has_more']
                questions += jsonResponse["items"]
                print len(questions), " questions in total, on page ", searchPayload['page'], "  any more? ",  moreQuestions
                searchPayload['page'] += 1

            if "error_id" in jsonResponse:
                raise APIException("StackExchange API Error:", jsonResponse["error_message"])

            if "backoff" in jsonResponse:
                time.sleep( int(searchPayload['backoff']) +  1 )

            elif "backoff" not in jsonResponse:
                time.sleep(0.1)

        # Get users IDs from question
        for question in questions:
            if 'user_id' in question['owner']:
                userId = str(question['owner']['user_id'])
                userIds.append(userId)

        numUserPages = int(math.ceil(float(len(userIds))/100))
        #print "userids len", len(userIds), "numUserPages",  numUserPages, math.ceil(numUserPages)
        userPages = split_list(userIds, numUserPages)

        #Cycle through user pages and get all the user details
        for page in userPages:
            usersString = ";".join(page)
            #Get all the users from the API
            users += requests.get(baseUserUrl + usersString, userPayload).json()["items"]

        for q in questions:
            #Get the user, check if they have a location
            user = get_question_user(q, users)
            if "question_id" not in question_ids:
                question_ids.append(q['question_id'])
                print "Question ID", q['question_id']
            else:
                break

            # Filter users that don't have have a UK location
            if user and len(filter(lambda l: l in user['location'], locs)):
                #print "UK User: ", user["display_name"], user["location"]

                output.append(
                    map((lambda x: parser.unescape(x) if type(x) == str else x ),[
                        q['title'],
                        q['link'],
                        time.strftime("%d/%m/%y", time.localtime(float(user['last_access_date']))),
                        q['is_answered'],
                        user['display_name'],
                        user['link'],
                        user['location'],
                        user['reputation']
                    ])
                )

    write_csv(csvFile, output)


def split_list(alist, parts=1):
    length = len(alist)
    return [ alist[i*length // parts: (i+1)*length // parts]
             for i in range(parts) ]


def get_question_user(question, users):
    user = filter(( lambda u: 'user_id' in u and 'user_id' in question['owner'] and
                    u['user_id'] == question['owner']['user_id'] and "location" in u ), users )
    if len(user) == 1:
        return user[0]

def write_csv(csvName, outputRows):
    with open(csvName, 'wb') as fp:
            seCSV = csv.writer(fp, delimiter=',')
            print "Writing headers to" + csvName +  "..."
            headers = [ ["Title","Link","Date","Answered","User","Profile Link","Location","Reputation"] ]
            seCSV.writerows(headers)
            print "Writing out output to" + csvName +  "..."
            seCSV.writerows(outputRows)
            print "Done!"

if __name__ == "__main__":

    site = 'stackoverflow' #gis
    locs = ["United Kingdom", "UK", "England", "Wales", "Scotland", "Great Britain", "GB"]
    keyword = "arcgis"
    startDate = 1412121600
    endDate = int(round(time.time(), 0))
    fields = [ "tagged", "title", "body" ]
    csvName = keyword

    checkStackExchange(csvName, fields, startDate, endDate, locs, site, keyword)



