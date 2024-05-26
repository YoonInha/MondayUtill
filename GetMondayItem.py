import requests
import pandas as pd
import argparse
import csv
import json

# ArgumentParser 객체 생성
parser = argparse.ArgumentParser(description="Monday.com GraphQL Query CLI")
# 필요한 파라미터 추가
parser.add_argument('--board_id', type=int, required=True, help='ID of the Monday.com board')
# 파라미터 파싱
args = parser.parse_args()
# 파싱된 파라미터 사용
board_id = args.board_id

with open('config.json') as f:
    config = json.load(f)

# Monday.com OAuth2 설정
client_id = config['client_id']
client_secret = config['client_secret']
redirect_uri = config['redirect_uri']
token_url = 'https://auth.monday.com/oauth2/token'
api_url = 'https://api.monday.com/v2'

# Step 1: 사용자 인증 요청 URL 생성
authorization_base_url = 'https://auth.monday.com/oauth2/authorize'
authorization_url = f"{authorization_base_url}?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code"
print(f"다음 URL을 브라우저에서 여세요: {authorization_url}")

# Step 2: 사용자가 인증한 후 리디렉션된 URL에서 인증 코드 추출
auth_code = input("브라우저에서 복사한 인증 코드를 입력하세요: ")

# Step 3: 인증 코드를 사용하여 액세스 토큰 요청
token_data = {
    'client_id': client_id,
    'client_secret': client_secret,
    'redirect_uri': redirect_uri,
    'code': auth_code,
    'grant_type': 'authorization_code'
}
token_response = requests.post(token_url, data=token_data)
token_response.raise_for_status()
tokens = token_response.json()
access_token = tokens['access_token']

parser = argparse.ArgumentParser(description="Monday.com GraphQL Query CLI")
parser.add_argument('--board_id', type=int, required=True, help='ID of the Monday.com board')
args = parser.parse_args()
board_id = args.board_id

# Step 4: Monday.com API를 사용하여 아이템 가져오기
headers = {
    'Authorization': access_token,
    'Content-Type': 'application/json'
}

# 특정 보드의 아이템을 가져오는 GraphQL 쿼리
query = f'''
{{
  boards (ids: {board_id}) {{
    name
    state
    items_page {{
      items {{
        name
        column_values{{
          text
        }}
        group{{
          title
        }}
        subitems {{
          board {{
            name
          }}
          name
          column_values {{
            text
          }}
        }}
      }}
    }}
  }}
}}
'''

response = requests.post(api_url, headers=headers, json={'query': query})
response.raise_for_status()
data = response.json()

# Step 5: 데이터를 CSV로 저장
items = data['data']['boards'][0]['items_page']['items']
item_data = len(items)
df = pd.json_normalize(items)

persons = {}
projects = {}
doneworks = []
todoworks = []
notes = []

for item in items:
    # print(item)
    person_name = item['group']['title']
    project_name = item['name']
    done_work = item['column_values'][1]['text']
    todo_work = item['column_values'][2]['text']
    note = item['column_values'][3]['text']

    print('person :::: '+ person_name)
    print('project :::: '+ project_name)

    print('----------------')
    # persons 딕셔너리에 데이터 추가
    if person_name not in persons:
        persons[person_name] = {"projects": {}}
    
    # projects 딕셔너리에 데이터 추가
    if project_name not in projects:
        projects[project_name] = {"done_work": [], "todo_work": [], "note":[]}
    if (done_work != ""):
        doneworks.append(done_work)
        projects[item['name']]["done_work"].append(doneworks)
    if (todo_work != ""):
        todoworks.append(todo_work)
        projects[item['name']]["todo_work"].append(todoworks)
    if (note != ""):
        notes.append(note)
        projects[item['name']]["note"].append(notes)
    # done_work, todoworks 배열에 데이터 추가
    for subitem in item['subitems']:
        doneworks = []
        todoworks = []
        notes = []

        if subitem['column_values'][0]['text'] != "":
            doneworks.append(subitem['column_values'][0]['text'])
            projects[subitem['name']]["done_work"].append(doneworks)
        if subitem['column_values'][1]['text'] != "":
            todoworks.append(subitem['column_values'][1]['text'])
            projects[subitem['name']]["todo_work"].append(todoworks)
        if subitem['column_values'][2]['text'] != "":
            notes.append(subitem['column_values'][2]['text'])
            projects[subitem['name']]["note"].append(notes)
    print(doneworks)
    print(todoworks)
    print(notes)
    print('+++++++++++++++')

    # persons 딕셔너리에 프로젝트 추가
    persons[person_name]["projects"][project_name] = projects[project_name]
print('$$$$$$$$$$$$$$$$')
print(persons)
print('$$$$$$$$$$$$$$$$')

filename = data['data']['boards'][0]['name'] + '.csv'

with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['이름', '프로젝트', '한 일', '할 일', '비고']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for name, projects in persons.items():
        for project, tasks in projects['projects'].items():
            done_tasks = tasks['done_work']
            todo_tasks = tasks['todo_work']
            notes = tasks['note']

            # 각각의 작업 수만큼 행 추가
            max_len = max(len(done_tasks), len(todo_tasks), len(notes))
            for i in range(max_len):
                done_task = done_tasks[i][0] if i < len(done_tasks) else ''
                todo_task = todo_tasks[i][0] if i < len(todo_tasks) else ''
                note = notes[i][0] if i < len(notes) else ''
                writer.writerow({'이름': name, '프로젝트': project, '한 일': done_task, '할 일': todo_task, '비고': note})

print("CSV 파일로 저장되었습니다: " + filename)
