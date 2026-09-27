import requests
from bs4 import BeautifulSoup
html = requests.get('https://github.com/users/virajpotdar/contributions', timeout=20, headers={'User-Agent':'Mozilla/5.0'}).text
soup = BeautifulSoup(html, 'html.parser')
for tag in soup.select('td,rect,span,div'):
    attrs = tag.attrs
    if 'data-date' in attrs or 'aria-label' in attrs or ('class' in attrs and 'ContributionCalendar' in ' '.join(tag.get('class', []))):
        print(tag.name, attrs)
        break
