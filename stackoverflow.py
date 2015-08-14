__author__ = 'JMilner'

import requests
import time
import csv

class APIException(Exception):
    pass

def checkStackExchange(startDate, endDate, locs, site, intitle):

    baseSearchUrl = "http://api.stackexchange.com/2.2/search"
    baseUserUrl = "http://api.stackexchange.com/2.2/users/"

    print startDate,endDate

    searchPayload = {
        'fromdate' : startDate,
        'todate' : endDate,
        'order' : "desc",
        'sort' : "activity",
        'intitle' : intitle,
        'site' : site
    }

    userPayload = {
        'order' : 'desc',
        'sort' : 'reputation',
        'site' : site
    }

    response = requests.get(baseSearchUrl, params=searchPayload)
    jsonResponse = response.json()
    if "error_id" not in jsonResponse:
        questions = jsonResponse["items"]
        userIds = "{"
        with open('test.csv', 'wb') as fp:
            seCSV = csv.writer(fp, delimiter=',')
            headers = [ ["Title","Link","Date","Answered","User","Profile Link","Location","Reputation"] ]
            seCSV.writerows(headers)
            c = 0

            # Get users IDs from questions
            for question in questions:
                if 'user_id' in question['owner']:
                    userId = str(question['owner']['user_id'])
                    userIds + ";" + userId

            #Get all the users from the API
            users = requests.get(baseUserUrl + userIds, userPayload).json()['items'][0]


            for q in questions:
                #Get the user, check if they have a location
                user = filter( (lambda u: u['user_id'] == q['user_id'] && 'location' in u), users)[0]

                if user and 'location' in user:
                    print "location found", user["user_id"], user["location"]

                # Filter users that don't have have a UK location
                if len(filter(lambda l: l in user['location'], locs)):

                    output = [
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
                             ]
                    seCSV.writerows(output)
    else:
        raise APIException("StackExchange API Error:", jsonResponse["error_message"])


if __name__ == "__main__":

    site = 'stackoverflow'
    locs = ["United Kingdom", "UK", "England", "Wales", "Scotland", "Great Britain", "GB"]
    intitle = "arcgis"
    startDate = 1412121600
    endDate = int(round(time.time(), 0))

    checkStackExchange(startDate, endDate, locs, site, intitle)



