# Scrape StackOverflow for questions and save the results in csv and json files
# Author: MEYLAN ERIC 2024-02-01
import requests
from bs4 import BeautifulSoup
import json
from typing import List


def get_rep_form_text(text: str = ''):
    rep = ''
    for n in text:
        if n.isdigit():
            rep = n + rep
        elif n == ',':
            continue
        else:
            break
    try:
        rep = int(rep)
    except ValueError:
        rep = 0
    return rep


def convert_to_int(string_to_convert: str = ''):
    suffixes = {
        'k': 1000,
        'm': 1000000
    }
    string_to_convert = string_to_convert.lower()
    multiplier = 1  # Default value
    if string_to_convert[-1] in suffixes:
        multiplier = suffixes[string_to_convert[-1]]  # Get the last char of the str
        string_to_convert = string_to_convert[:-1]  # Remove the suffix
    try:
        number = float(string_to_convert)
        return int(number * multiplier)
    except ValueError:
        return 0


class Scraper:
    # region Constants
    # Questions list
    div_id_questions: str = 'questions'
    div_id_question: str = 'question-summary-'  # + id
    div_class_question: str = 's-post-summary'
    div_class_content: str = 's-post-summary--content'
    h3_class_question_title: str = 's-post-summary--content-title'
    div_class_text: str = 's-post-summary--content-excerpt'
    div_class_stats: str = 's-post-summary--stats'
    div_class_metadata: str = 's-post-summary--meta'
    div_class_userinfo: str = 's-user-card'
    div_class_tags: str = 's-post-summary--meta-tags'
    a_class_tag: str = 'post-tag'
    time_class_date: str = 's-user-card--time'
    # Answers list

    # Set the url and parameters
    base_url: str = 'https://stackoverflow.com/questions'
    sorts: dict = dict.fromkeys(['Newest', 'RecentActivity', 'MostVotes', 'MostFrequent', 'BountyEndingSoon'], 'sort=')
    filters: dict = dict.fromkeys(['NoAnswers', 'NoAcceptedAnswer', 'Bounty', ], 'filters=')
    tabs: dict = dict.fromkeys(['Newest', 'Active', 'Bounties', 'Unanswered', 'Frequent', 'Votes'], 'tab=')
    page_prefix: str = 'page='
    search_tag_dictionary: dict = dict.fromkeys('#', '%23')
    illegal_characters: list = None
    # endregion

    def __init__(self):
        self.illegal_characters = ['?', '%', '*', ';', '@', '&', '=', '+',
                                   '$', ',', '/', '[', ']', '(', ')',
                                   '|', '~', '`', '<', '>']

    # region Functions

    def get_questions(self, rel_url: str = ''):

        url = self.base_url + rel_url
        page = requests.get(url)
        soup = BeautifulSoup(page.text, 'html.parser')
        questions_div_element = soup.find('div', id=self.div_id_questions)
        questions_by_id = questions_div_element.find_all('div', id=lambda x: x and x.startswith(self.div_id_question))

        questions_arr = []
        for question in questions_by_id[:10]:
            # Elements
            title_element = question.find('h3', class_=self.h3_class_question_title)
            stats_element = question.find('div', class_=self.div_class_stats)
            metadata_element = question.find('div', class_=self.div_class_metadata)
            tags_element = metadata_element.find('div', class_=self.div_class_tags)
            user_element = metadata_element.find('div', class_=self.div_class_userinfo)
            time_element = metadata_element.find('time', class_=self.time_class_date)
            # Content
            title = title_element.text.strip()
            link = title_element.find('a')['href']
            text = question.find('div', class_=self.div_class_text).text.strip()
            # Stats
            if stats_element.find('div', class_='has-accepted-answer') is not None:
                accepted_answer = True
            else:
                accepted_answer = False
            stats = stats_element.find_all('span', class_='s-post-summary--stats-item-number')
            votes = stats[0].text
            answers = stats[1].text
            views = stats[2].text
            # stats_units = stats_element.find_all('span', class_='s-post-summary--stats-item-unit')
            # votes_unit = stats_units[0].text
            # answers_unit = stats_units[1].text
            # views_unit = stats_units[2].text
            # views_int = convert_to_int(views)
            q_id = question['id'].replace(self.div_id_question, '')
            # Tags
            tags = tags_element.find_all('a', class_=self.a_class_tag)
            tags = [tag.text for tag in tags]
            # User
            reputation_text = ''
            if user_element.find('div', class_='s-user-card--link').find('a') is not None:
                user_name = user_element.find('div', class_='s-user-card--link').find('a').text
                user_id = user_element.find('a', class_='s-avatar')['data-user-id']
                reputation_text = user_element.find('li', class_='s-user-card--rep').find('span')['title']
                rep = get_rep_form_text(reputation_text)
                time = time_element.find('span')['title']
            else:
                user_name = user_element.find('div', class_='s-user-card--link').text
                user_id = q_id
                rep = 0
                time = 0
            # Create the question
            question = {
                'question_id': q_id,
                'title': title,
                'link': link,
                'text': text,
                'excerpt': '',
                'question_date': time,
                'votes': votes,
                'has_accepted_answer': accepted_answer,
                'answers_amount': answers,
                'views': views,
                'tags': tags,
                'user_name': user_name,
                'user_id': user_id,
                'reputation': reputation_text,
                'accepted_answer': None,
                'all_answers': None
            }
            questions_arr.append(question)
            # Create json file and format the data properly
            with open('question_list.json', 'w') as file:
                json.dump(questions_arr, file, default=lambda o: o.__dict__, indent=4)
        return questions_arr

    def get_answers(self, question_id):
        url = self.base_url + '/' + question_id
        page = requests.get(url)
        soup = BeautifulSoup(page.text, 'html.parser')
        header_elements = soup.find('div', id='content').find('div', class_='inner-content').findAll('div', class_='d-flex')
        question_details_element = header_elements[1]
        main_element = soup.find('div', id='mainbar')
        question_element = main_element.find('div', id='question')
        answers_element = main_element.find('div', id='answers')
        question_title = header_elements[0].find('h1').find('a').text
        # Question info
        question_details = question_details_element.findAll('div', class_='flex--item')
        question_time = question_details[0]['title']
        question_modified = question_details[1].find('a')['title']
        question_views = question_details[2]['title']
        question_votes = question_element['data-score']
        question_id = question_element['data-questionid']
        question_content = question_element.find('div', class_='s-prose').text
        question_tags = question_element.findAll('a', class_='post-tag')
        question_tags = [tag.text for tag in question_tags]
        question_user = question_element.find('div', class_='user-details').find('a')
        question_user_rep = question_element.find('span', class_='reputation-score')['title']
        question_user_rep_int = get_rep_form_text(question_user_rep)
        question_user_badges = question_element.find('div', class_='-flair').findAll('span', class_='v-visible-sr')
        question_user_badges = [badge.text for badge in question_user_badges]

        # Answers
        answer_accepted = None
        has_accepted = False
        all_answers = answers_element.findAll('div', id=lambda x: x and x.startswith('answer-'))
        answer_id = ''
        answer_votes = ''
        answer_text = ''
        for answer in all_answers:
            if answer['data-highest-scored'] == '1':
                answer_id = answer['data-answerid']
                answer_content = answer.find('div', class_='s-prose')
                answer_votes = answer['data-score']
                answer_text = answer_content.text

        question = {
            'question_id': question_id,
            'title': question_title,
            'link': f'/questions/{question_id}',
            'text': question_content,
            'excerpt': '',
            'question_date': question_time,
            'votes': question_votes,
            'has_accepted_answer': has_accepted,
            'answers_amount': len(all_answers),
            'views': question_views,
            'tags': question_tags,
            'user_name': question_user.text,
            'user_id': question_user['href'],
            'reputation': question_user_rep,
            'accepted_answer': {
                'id': answer_id,
                'link': f'/questions/{question_id}',
                'body': answer_text,
                'creation_date': '',
                'modification_date': '',
                'votes': answer_votes,
                'is_accepted': answer_accepted,
                'user_id': '',
                'user_name': '',
                'user_reputation': 0,
                'question_id': question_id
            },
            'all_answers': []

        }
        with open(f'question_{question_id}.json', 'w') as file:
            json.dump(question, file, indent=4)
        return question

    def get_comments(self, answer_id: str = ''):
        pass

    def remove_illegal_chars(self, tag: str = ''):
        tag = ''.join(filter(lambda x: x not in self.illegal_characters, tag))
        for k, v in self.search_tag_dictionary.items():
            if k in tag:
                tag = tag.replace(k, v)
        return tag
    # endregion


if __name__ == "__main__":
    s = Scraper()
    test = s.get_answers('27928372')
    print(test)
