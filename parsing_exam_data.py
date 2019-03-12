import requests
from bs4 import BeautifulSoup
import json

base_url = 'http://postyplenie.ru/calculator.php?Vuz=all&"'
subjects_set = {'obzestvoznanie', 'russkiy', 'informatika', 'biologiya', 'geografiya',
                'ximiya', 'fizika', 'literatura', 'history', 'matematika', 'lang'}
subjects_translate = {'obzestvoznanie': "Обществознание", 'russkiy': "Русский язык",
                      'informatika': "Информатика", 'biologiya': "Биология",
                      'geografiya': "География", 'ximiya': "Химия",
                      'fizika': "Физика", 'literatura': "Литература",
                      'history': "История", 'matematika': "Математика", 'lang':"Английский язык"}
end_url = 'Submit.x=60&Submit.y=23'

spec_id_dict = {}
id_spec_dict = {}

specs_url = 'https://moeobrazovanie.ru/specialities_vuz/'
r = requests.get(specs_url)
text = r.text
soup = BeautifulSoup(text, 'html.parser')
for a in soup.find_all("a"):
    if a.get('class') == ['spec_articles_list_spec_link']:
        link = a.get('href').split('/')[-1]
        new_url = specs_url + link
        r = requests.get(new_url)
        text = r.text
        soup_new = BeautifulSoup(text, 'html.parser')
        name = soup_new.find_all("h1")[1].get_text()
        for td in soup_new.find_all("td"):
            if td.get_text().startswith("Код") \
                    and not td.get('class') == ['specHelmImg']:
                id = str(list(td.children)[0]).split(" ")[-1]
                break
        spec_id_dict[name] = [id]
        id_spec_dict[id] = name

js = open('speciality_id.json', encoding='utf-8').read()
id_spec_dict = json.loads(js)

middle_url = ""
list_subjects = []
for item in subjects_set:
    middle_url += item + "=100&"
url = base_url + middle_url + end_url
url = url.replace('"', '')

r = requests.get(url)
text = r.text

universities = dict()
list_universities = []
list_grades = []
list_specs = []
list_ids = []
count_subjects = []
soup = BeautifulSoup(text, 'html.parser')
for td in soup.find_all('td'):
    if td.get('class') == ['light_gray_blue']:
        list_universities.append(td.get_text())
    if td.get('style') == 'white-space:nowrap;':
        list_grades.append(td.get_text())
    if td.get('class') == ['light_gray_back', 'gray_border_right']:
        list_ids.append(td.get_text())
    if td.find('div') != None and \
            td.find('div').get("class") == ['small_text', 'gray_text']:
        subjects = td.find('div').get_text()
        list_subjects.append(subjects)
        count_subjects.append(len(str(subjects).split(",")))

for i in range(len(list_universities)):
    try:
        if list_universities[i] in universities:
            universities[list_universities[i]].append((id_spec_dict[list_ids[i]], list_ids[i],
                                                       list_grades[i], list_subjects[i],
                                                       count_subjects[i]))
        else:
            universities[list_universities[i]] = [(id_spec_dict[list_ids[i]], list_ids[i],
                                                   list_grades[i], list_subjects[i],
                                                   count_subjects[i])]
    except KeyError:
        if list_universities[i] in universities:
            universities[list_universities[i]].append(("", list_ids[i],
                                                       list_grades[i], list_subjects[i],
                                                       count_subjects[i]))
        else:
            universities[list_universities[i]] = [("", list_ids[i],
                                                   list_grades[i], list_subjects[i],
                                                   count_subjects[i])]


with open('universities.json', 'w', encoding="utf-8") as fp:
    json.dump(universities, fp, ensure_ascii=False, indent=4, separators=(',', ': '))

new_url = 'https://www.ucheba.ru/for-abiturients/speciality'
r = requests.get(new_url)
text = r.text
soup = BeautifulSoup(text, 'html.parser')
for div in soup.find_all("div"):
    if div.get('class') == ['col-sm-4', 'fs-large', 'mb-15']:
        speciality_id = str(div.find('a').get('href')).split('/')[-1]
        speciality_name = div.get_text().replace("\n", "")

        url_speciality = new_url + "/" + str(speciality_id)
        r = requests.get(url_speciality)
        text = r.text
        soup_speciality = BeautifulSoup(text, 'html.parser')
        for div_spec in soup_speciality.find_all("div"):
            if div_spec.get('class') == ['mb-section']:
                for h2 in div_spec.find_all('h2'):
                    if h2.get_text() == 'Кем работать':
                        spec_descr = div_spec.get_text().replace("\n", "").\
                            replace("Кем работать", "").replace("\t", "")
                    if h2.get_text() == 'Перспективы':
                        spec_perspecs = div_spec.get_text().replace("\n", "").\
                            replace("Перспективы", "").replace("\t", "")

        try:
            spec_id_dict[speciality_name].append((spec_descr, spec_perspecs))
        except KeyError:
            continue

with open('speciality.json', 'w', encoding="utf-8") as fp:
    json.dump(spec_id_dict, fp, ensure_ascii=False, indent=4, separators=(',', ': '))