import requests
from bs4 import BeautifulSoup
import pprint   #   Prety Print

#   Connecting to the News Hacker website
res = requests.get('https://au.indeed.com/')
soup = BeautifulSoup(res.text, 'html.parser')

links = soup.select('.jcs-JobTitle > a')
titles = soup.select('.jobTitle')


#   Sorting
def sort_stories(hnlist):
    #return sorted(hnlist, key=lambda k: k['votes'], reverse=True)
    return hnlist.sort()


def create_custom_job(links, titles):
    jobs = []
    for idx, item in enumerate(links):
        title = item.getText()
        href = item.get('href', None)

        if True:
            jobs.append({'title': title, 'link': href})
    return sort_stories(jobs)


pprint.pprint(create_custom_job(links, titles))
