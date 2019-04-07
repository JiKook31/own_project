import re
import requests
import json
import datetime
import csv
import spacy

base_url = 'https://api.hh.ru/vacancies'
specs_list = []


def parse_all_vacancies(start_time, end_time, to_continue=False):
    """
    uses hh API and parses all existing vacancies in time slot from start_time to end_time
    :param start_time: time in format "yyyy-mm-ddThh:mm:ss" from which the parsing starts
    :param end_time: time in format "yyyy-mm-ddThh:mm:ss" until which the parsing ends
    :return: nothing, "vacancies.csv" is created with following structure:
    "ID, Name, City, Avg salary, Decription, Specalizations"
    """
    start_date = datetime.datetime.strptime(start_time, '%Y-%m-%d')
    from_date = start_date
    to_date = start_date + datetime.timedelta(hours=4)
    end_date = datetime.datetime.strptime(end_time, '%Y-%m-%d')

    list_id = set()
    params = {}
    write_mode = "w"

    with open("../specializations/specialities.csv", encoding='utf-8') as specs_csv:
        csv_reader = csv.reader(specs_csv, delimiter=',')
        for row in list(csv_reader)[1:]:
            specs_list.append((row[1], row[2]))

    if to_continue:
        write_mode = "a"
        with open('vacancies/vacancies.csv', encoding='utf-8') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in list(csv_reader)[1:]:
                list_id.add(row[0])

    with open('vacancies/vacancies.csv', write_mode, encoding='utf-8') as f:
        if write_mode == 'w':
            f.write("ID, Name, City, Avg salary, Decription, Specalizations\n")

        while to_date <= end_date:
            url = base_url + f'?date_from=%s&date_to=%s' \
                  % (from_date.isoformat(), to_date.isoformat())
            to_date += datetime.timedelta(hours=4)
            from_date += datetime.timedelta(hours=4)

            r = requests.get(url)
            text_json = json.loads(r.text)
            params['per_page'] = text_json['per_page']

            if text_json['found'] == 0:
                continue

            for i in range(text_json['pages']):
                params['page'] = i
                r = requests.get(base_url, params)
                if 200 != r.status_code:
                    break
                data = json.loads(r.text)['items']
                for vacancy in data:
                    prev_len = len(list_id)
                    vacancy_id = vacancy['id']
                    list_id.add(vacancy_id)
                    if prev_len < len(list_id):
                        parse_vacancy(vacancy_id, f)


def parse_vacancy(vac_id, file):
    """
    parse one vacancy by id and paste the row with information to the file
    :param vac_id: id of the vacancy that needs to be parsed
    :param file: file to which the row with all the information should be inserted
    :return: nothing
    """
    url = base_url + f'/%s' % vac_id
    r = requests.get(url)
    vacancy = json.loads(r.text)

    try:
        salary_from = converting_salary(vacancy['salary']['from'])
        salary_to = converting_salary(vacancy['salary']['to'])
    except TypeError:
        salary_from = salary_to = 0
    if salary_from == 0 or salary_to == 0:
        salary_avg = salary_from if salary_to == 0 else salary_to
    else:
        salary_avg = salary_from + abs(salary_to - salary_from) / 2
    description = vacancy['description']
    cleanr = re.compile('<.*?>')
    description = re.sub(cleanr, '', description)

    best_specs = map_vacancy_spec(description)

    file.write('"%s","%s","%s",%i,"%s","%s"\n' %
               (vac_id, vacancy['name'].replace('"', ""),
                vacancy['area']['name'], salary_avg,
                description.replace('"', "") if description is not None else "",
                best_specs))


def converting_salary(salary):
    """
    salary is converted to int or declared to 0 if it's None
    :param salary: string that has to be converted to int
    :return: converted int, 0 if None
    """
    if salary is not None:
        salary = int(salary)
    else:
        salary = 0
    return salary


def map_vacancy_spec(vacancy_desc):
    """
    for vacancy description gives 3 the most similar specialization descriptions
    :param vacancy_desc: description of the vacancy that has to be mapped with specializations
    :param specs_list: list of tuples: (id of specialization, specialization's description)
    :return: list of 3 most similar specializations
    """
    nlp = spacy.load('en_core_web_sm', vectors='./tmp')

    similarity_measures = []

    vacancy_desc = nlp(vacancy_desc)
    for spec in specs_list:
        vac_spec_sim = vacancy_desc.similarity(nlp(spec[1]))
        similarity_measures.append((vac_spec_sim, spec[0]))

    result = []
    i = 1
    for similar in sorted(similarity_measures, reverse=True):
        if i < 4:
            result.append(similar[1])
        i += 1
    return result


# from gensim.models import KeyedVectors
# model = KeyedVectors.load_word2vec_format('model.bin', binary=True)
# model.wv.save_word2vec_format('vec_model.txt')

# parse_all_vacancies("2019-01-01", "2019-03-30", to_continue=True)