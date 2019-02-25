import requests
from bs4 import BeautifulSoup

url = 'http://postyplenie.ru/calculator.php?Vuz=all&obzestvoznanie=&russkiy=85&informatika=&biologiya=65&geografiya=&ximiya=&fizika=&literatura=&history=&matematika=75&lang=&Submit.x=60&Submit.y=23'
r = requests.get(url)
text = r.text

universities = dict()
list_universities = []
list_grades = []
list_specs = []
soup = BeautifulSoup(text, 'html.parser')
for td in soup.find_all('td'):
    if td.get('class') == ['light_gray_blue']:
        list_universities.append(td.get_text())
    if td.get('style') == 'white-space:nowrap;':
        list_grades.append(td.get_text())
    if td.get('class') == ['gray_border_right']:
        list_specs.append(td.get_text().replace('\n', ''))

for i in range(len(list_universities)):
    if list_universities[i] in universities:
        universities[list_universities[i]].append((list_specs[i], list_grades[i]))
    else:
        universities[list_universities[i]] = [(list_specs[i], list_grades[i])]

print(universities)