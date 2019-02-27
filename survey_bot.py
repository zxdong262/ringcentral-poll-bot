"""
survey bot logic
"""

from shortid import ShortId
from functools import reduce
import pydash as _
import re
import os
import sqlite_custom as sq
from datetime import datetime

sid = ShortId()
gid = sid.generate

def helpMsg(botId):
  return f'''Hello, I am the survey bot.

To Add new Survey, just Reply:


> @![:Person]({botId}) **1** **add** **Your Survey title**
> Survey option 1
> Survey option 2
> Survey option 3


* If you want to add **multi choice question**, change **1** to **N**, or you can just skip **1**.
* You can view survey list by **@![:Person]({botId}) list**.
* You can remove survey by **@![:Person]({botId}) remove #surveyID**.

'''

def surveyReducer(x, y):
  s1 = f'{y["index"]}. {y["title"]} ({len(y["userIds"])})'
  return f'{x}{s1}\n'

def surveyListReducer(x, y):
  s1 = f'* #{y["id"]} {y["title"]} (by ![:Person]({y["creatorId"]}))'
  return f'{x}{s1}\n'

def alreadySelected(options, id):
  '''
  check if userid already made choices
  '''
  for opt in options:
    userIds = opt['userIds'] or []
    if id in userIds:
      return True
  return False

def onSurveyList(
  bot,
  groupId,
  text,
  sendMsg,
  dbAction
):
  '''
  survey list command
  '''
  surveys = dbAction('survey', 'get', {
    'key': 'groupId',
    'value': groupId
  })
  if not _.predicates.is_list(surveys):
    surveys = []
  surveyList = reduce(surveyListReducer, surveys, '')
  if surveyList == '':
    return sendMsg(helpMsg(bot.id))
  return sendMsg(
    f'''
**Survey list in this group:**

{surveyList}

Reply with **@![:Person]({bot.id}) show #SurveyID** to show Survey info.
Reply with **@![:Person]({bot.id}) remove #SurveyID** to delete one survey.
'''
  )

def onRemoveSurvey(
  m,
  dbAction,
  sendMsg
):
  '''
  survey remove command
  '''
  id = m.group(1)
  sur = dbAction('survey', 'get', {
    'id': id
  })
  if not _.predicates.is_object(sur):
    return sendMsg(f'Survey **{id}** not exist')
  dbAction('survey', 'remove', {
    'id': id
  })
  return sendMsg(f'Survey **#{id}** {sur["title"]} deleted')

def onShowSurvey(
  m,
  dbAction,
  sendMsg,
  bot
):
  '''
  survey show command
  '''
  id = m.group(1)
  sur = dbAction('survey', 'get', {
    'id': id
  })
  if not _.predicates.is_object(sur):
    return sendMsg(f'Survey **#{id}** not exist')
  arr = sur['options']
  if not _.predicates.is_list(arr):
    arr = []
  lister = reduce(surveyReducer, arr, '')
  return sendMsg(
    f'''
Survey **#{id}**

**{sur['title']}**

{lister}

Reply "@![:Person]({bot.id}) #{id} **1**" to vote.
    '''
  )

def onAddSurvey(
  re1,
  arr,
  groupId,
  creatorId,
  dbAction,
  bot,
  sendMsg
):
  '''
  survey add command
  '''
  maxSelect = int(re1.group(1) or 1)
  title = re1.group(2) or 'untitled survey'
  i = 0
  res = {
    'id': gid(),
    'max_select': maxSelect,
    'groupId': groupId,
    'creatorId': creatorId,
    'options': [],
    'title': title
  }
  for tx in arr:
    if i == 0 or tx.strip() == '':
      i = i + 1
      continue
    else:
      res['options'].append({
        'title': tx,
        'userIds': [],
        'index': i
      })
      i = i + 1
  dbAction('survey', 'add', res)
  arr = res['options']
  if not _.predicates.is_list(arr):
    arr = []
  list1 = reduce(surveyReducer, arr, '')
  selectString = '1'
  if maxSelect > 1:
    selectString = f'1,2,..N({maxSelect} choices max)'
  msg = f'''@![:Person]({creatorId}) New survey added:

**Survey #{res['id']}**

**{title}**

{list1}

Reply "@![:Person]({bot.id}) #{res['id']} **{selectString}**" to vote.
'''
  sendMsg(msg)
  return

def onVote(
  text,
  dbAction,
  creatorId,
  sendMsg,
  bot,
  msgHelp
):
  '''
  on vote for survey
  '''
  m = re.match(r'.+ #([^ ]+) +([\d,]+)', text)
  if not m is None:
    try:
      uid = m.group(1)
      indexs = m.group(2)
      indexArr = indexs.split(',')
      res = dbAction('survey', 'get', {
        'id': uid
      })
      if alreadySelected(res['options'], creatorId):
        return sendMsg(
          f'@![:Person]({creatorId}) you already made your choices'
        )
      if len(indexArr) > res['max_select']:
        return sendMsg(
          f'@![:Person]({creatorId}) max {res["max_select"]} choices'
        )
      if not _.predicates.is_dict(res):
        return sendMsg(
          f'@![:Person]({creatorId}) Survey not exist, please check the Survey ID'
        )

      for index in indexArr:
        index = int(index)
        rindex = index - 1
        opt = _.get(res, f'options[{rindex}]')
        if opt is None:
          return sendMsg(
            f'@![:Person]({creatorId}) Survey Option **{index}** not exist, please check Option index number you select'
          )
        res['options'][rindex]['userIds'] = _.arrays.uniq(
          res['options'][rindex]['userIds'] + [creatorId]
        )
      dbAction('survey', 'update', {
        'id': uid,
        'update': {
          'options': res['options']
        }
      })
      arr = res['options']
      if not _.predicates.is_list(arr):
        arr = []
      list1 = reduce(surveyReducer, arr, '')
      selectString = '1'
      if res['max_select'] > 1:
        selectString = f'1,2,..N({res["max_select"]} choices max)'
      msg = f'''@![:Person]({creatorId}) your vote added:

**Survey #{res['id']}**

**{res['title']}**

{list1}

Update time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

Reply "@![:Person]({bot.id}) #{res['id']} **{selectString}**" to vote.
'''
      sendMsg(msg)
    except Exception as e:
      print('error', e)
      return
  else:
    sendMsg(msgHelp)

dbTablesDef = [
  {
    'name': 'bot',
    'schemas': [
      {
        'name': 'id',
        'type': 'string',
        'primary': True
      },
      {
        'name': 'token',
        'type': 'json'
      },
      {
        'name': 'data',
        'type': 'json'
      }
    ]
  },
  {
    'name': 'user',
    'schemas': [
      {
        'name': 'id',
        'type': 'string',
        'primary': True
      },
      {
        'name': 'token',
        'type': 'json'
      },
      {
        'name': 'groups',
        'type': 'json'
      },
      {
        'name': 'data',
        'type': 'json'
      }
    ]
  },
  {
    'name': 'survey',
    'schemas': [
      {
        'name': 'id',
        'type': 'string',
        'primary': True
      },
      {
        'name': 'options',
        'type': 'json'
      },
      {
        'name': 'title',
        'type': 'string'
      },
      {
        'name': 'groupId',
        'type': 'string'
      },
      {
        'name': 'creatorId',
        'type': 'string'
      },
      {
        'name': 'max_select',
        'type': 'string'
      }
    ]
  }
]
