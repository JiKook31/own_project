from itertools import chain, combinations

import requests
from bs4 import BeautifulSoup

def powerset(iterable):
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))

base_url = 'http://postyplenie.ru/calculator.php?Vuz=all&"'
subjects_set = {'obzestvoznanie', 'russkiy', 'informatika', 'biologiya', 'geografiya',
                'ximiya', 'fizika', 'literatura', 'history', 'matematika', 'lang'}
subjects_translate = {'obzestvoznanie': "Обществознание", 'russkiy': "Русский язык",
                      'informatika': "Информатика", 'biologiya': "Биология",
                      'geografiya': "География", 'ximiya': "Химия",
                      'fizika': "Физика", 'literatura': "Литература",
                      'history': "История", 'matematika': "Математика", 'lang':"Английский язык"}
end_url = 'Submit.x=60&Submit.y=23'

superset = powerset(subjects_set)

for set in superset:
    middle_url = ""
    list_subjects = []
    for item in set:
        middle_url += item + "=100&"
        list_subjects.append(subjects_translate[item])
    url = base_url + middle_url + end_url
    url = url.replace('"', '')

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
            universities[list_universities[i]].append((list_specs[i], list_grades[i], list_subjects))
        else:
            universities[list_universities[i]] = [(list_specs[i], list_grades[i], list_subjects)]
    if universities != {}:
        print(universities)
