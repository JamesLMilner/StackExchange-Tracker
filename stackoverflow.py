__author__ = 'JMilner'

import requests
import time
import csv
import math

class APIException(Exception):
    pass

def checkStackExchange(startDate, endDate, locs, site, keyword):

    baseSearchUrl = "http://api.stackexchange.com/2.2/search/advanced"
    baseUserUrl = "http://api.stackexchange.com/2.2/users/"

    print startDate,endDate

    searchPayload = {
        'pagesize' : 100,
        'page' : 1,
        'fromdate' : startDate,
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

    csvName = 'test' + '.csv'
    output = []
    questions = []
    userIds = []
    criteria = ["intitle", "tagged", "body"]
    previousCriteria = None

    for c in criteria:
        print c
        moreQuestions = True
        searchPayload[c] = keyword
        if previousCriteria:
            del searchPayload[previousCriteria]

        while moreQuestions:
            response = requests.get(baseSearchUrl, params=searchPayload)
            jsonResponse = response.json()

            if "error_id" not in jsonResponse and 'has_more' in jsonResponse:
                moreQuestions = jsonResponse['has_more']
                questions += jsonResponse["items"]
                print "The total number of questions is :", len(questions)
                searchPayload['page'] += 1

            else:
                raise APIException("StackExchange API Error:", jsonResponse["error_message"])


    # Get users IDs from question
    for question in questions:
        if 'user_id' in question['owner']:
            userId = str(question['owner']['user_id'])
            userIds.append(userId)

    numUserPages = int(math.ceil(float(len(userIds))/100))
    print "userids len", len(userIds), "numUserPages",  numUserPages, math.ceil(numUserPages)
    userPages = split_list(userIds, numUserPages)
   # print userPages

    for page in userPages:
        print "page length", len(page)
        usersString = ";".join(page)
        print baseUserUrl + usersString
        #Get all the users from the API
        users = requests.get(baseUserUrl + usersString, userPayload).json()["items"]
        print users
        print "user list", len(users)

        for q in questions:
            #Get the user, check if they have a location
            user = get_question_user(q, users)
            if user:
                print "user", user

            # Filter users that don't have have a UK location
            if user and len(filter(lambda l: l in user['location'], locs)):

                output.append(
                          [
                          q['title'],
                          q['link'],
                          time.strftime("%d/%m/%y", time.localtime(float(user['last_access_date'])) ),
                          q['is_answered'],
                          user['display_name'],
                          user['link'],
                          user['location'],
                          user['reputation']
                          ]
                    )

    write_csv(csvName, output)


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

    site = 'stackoverflow'
    locs = ["United Kingdom", "UK", "England", "Wales", "Scotland", "Great Britain", "GB"]
    intitle = "arcgis"
    startDate = 1412121600
    endDate = int(round(time.time(), 0))

    checkStackExchange(startDate, endDate, locs, site, intitle)



