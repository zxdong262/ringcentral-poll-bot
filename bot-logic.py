"""
sample config module
run "cp config.sample.py config.py" to create local config
edit config.py functions to override default bot behavior
"""
__name__ = 'localConfig'
__package__ = 'ringcentral_bot_framework'

from shortid import ShortId
from functools import reduce
import pydash as _
import re
try:
  import sqlite3
except:
  pass
import os
import sqlite_custom as sq

sid = ShortId()
gid = sid.generate

def helpMsg(botId):
  return f'''Hello, I am the survey bot.

To Add new Survey, just Reply:


> @![:Person]({botId}) **add**
> Beijing
> Shanghai
> Shenzhen
'''

def surveyReducer(x, y):
  s1 = f'{y["index"]}. {y["title"]} ({y["count"]})'
  return f'{x}{s1}\n'

def botJoinPrivateChatAction(bot, groupId, user, dbAction):
  """
  bot join private chat event handler
  bot could send some welcome message or help, or something else
  """
  bot.sendMessage(
    groupId,
    {
      'text': helpMsg(bot.id)
    }
  )

def botGotPostAddAction(
  bot,
  groupId,
  creatorId,
  user,
  text,
  dbAction,
  handledByExtension
):
  """
  bot got group chat message: text
  bot could send some response
  """

  if not f'![:Person]({bot.id})' in text:
    return

  arr = text.split('\n')
  txt1 = arr[0]
  msg = helpMsg(bot.id)

  if 'add' in txt1 and len(arr) < 3:
    return bot.sendMessage(groupId, {
      'text': msg
    })

  if 'add' in txt1:
    i = 0
    res = {
      'id': gid(),
      'max_select': 1,
      'options': []
    }
    for tx in arr:
      if i == 0 or tx.strip() == '':
        i = i + 1
        continue
      else:
        res['options'].append({
          'title': tx,
          'count': 0,
          'index': i
        })
        i = i + 1
    dbAction('survey', 'add', res)
    list1 = reduce(surveyReducer, res['options'], '')
    msg = f'''@![:Person]({creatorId}) New survey added:

**Survey #{res['id']}**
{list1}

Reply "@![:Person]({bot.id}) #{res['id']} **NUMBER**" to vote.
'''
    bot.sendMessage(groupId, {
      'text': msg
    })
    return

  m = re.match(r'.+ #([^ ]+) +(\d+)', text)
  if not m is None:
    try:
      uid = m.group(1)
      index = int(m.group(2))
      res = dbAction('survey', 'get', {
        'id': uid
      })
      if not _.predicates.is_dict(res):
        return bot.sendMessage(groupId, {
          'text': f'@![:Person]({creatorId}) Survey not exist, please check the Survey ID'
        })
      rindex = index - 1
      opt = _.get(res, f'options[{rindex}]')
      if opt is None:
        return bot.sendMessage(groupId, {
          'text': f'@![:Person]({creatorId}) Survey Option not exist, please check Option number you select'
        })
      res['options'][rindex]['count'] = res['options'][rindex]['count'] + 1
      dbAction('survey', 'update', {
        'id': uid,
        'update': {
          'options': res['options']
        }
      })
      list1 = reduce(surveyReducer, res['options'], '')
      msg = f'''@![:Person]({creatorId}) your vote added:

**Survey #{res['id']}**
{list1}

Reply "@![:Person]({bot.id}) #{res['id']} **NUMBER**" to vote.
'''
      bot.sendMessage(groupId, {
        'text': msg
      })
    except Exception as e:
      print('error', e)
      return

def dbTables():
  '''
  db tables to init
  '''
  return [
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
        }
      ]
    }
  ]


def dbWrapper(tableName, action, data = None):
  """custom db action wrapper
  * set DB_TYPE=custom in .env to activate
  * make sure it it stateless,
  * in every action, you should check database is ready or not, if not, init it first
  * check https://github.com/zxdong262/ringcentral-chatbot-python/blob/master/ringcentral_bot_framework/core/dynamodb.py or https://github.com/zxdong262/ringcentral-chatbot-python/blob/master/ringcentral_bot_framework/core/filedb.py as example
  * @param {String} tableName, user or bot, or other table you defined
  * @param {String} action, add, remove, update, get
  * @param {Object} data
  * for add, {'id': 'xxx', 'token': {...}, 'groups': {...}, 'data': {...}}
  * for remove, {'id': xxx} or {'ids': [...]}
  * for update, {'id': xxx, 'update': {...}}
  * for get, singleUser:{'id': xxx}, allUser: None
  """

  print(tableName, action, data)
  sq.prepareDb(dbTables())
  # try:
  id = None
  if 'id' in data:
    id = data['id']

  if action == 'add':
    sq.addOne(tableName, data)
    return 'added'

  elif action == 'remove':
    sq.delOne(tableName, id)
    return 'removed'

  elif action == 'update':
    update = data['update']
    sq.updateOne(tableName, id, update)
    return 'updated'

  elif action == 'get':
    return sq.getOne(tableName, id)

  # except Exception as e:
  #   print(e)
  #   return False

def dbName():
  '''
  return db name
  * set DB_TYPE=custom in .env to activate
  '''
  return 'sqlite3'