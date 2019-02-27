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
import os
try:
  import sqlite_custom as sq
except:
  pass
from survey_bot import helpMsg, onSurveyList, onRemoveSurvey, onShowSurvey, onAddSurvey, onVote, dbTablesDef

sid = ShortId()
gid = sid.generate

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

  if handledByExtension or not f'![:Person]({bot.id})' in text:
    return

  def sendMsg(txt):
    bot.sendMessage(groupId, {
      'text': txt
    })

  if text == f'![:Person]({bot.id}) list':
    return onSurveyList(
      bot,
      groupId,
      text,
      sendMsg,
      dbAction
    )

  m = re.match(r'^[^ ]+ +remove +#([^ ]+)$', text)
  if not m is None:
    return onRemoveSurvey(
      m,
      dbAction,
      sendMsg
    )

  m = re.match(r'^[^ ]+ +show +#([^ ]+)$', text)
  if not m is None:
    return onShowSurvey(
      m,
      dbAction,
      sendMsg,
      bot
    )

  arr = text.split('\n')
  txt1 = arr[0]
  msgHelp = helpMsg(bot.id)
  re1 = re.match(r'[^ ]+( +\d+)? +add( +.+)?', txt1)
  isAdding = not re1 is None
  if isAdding and len(arr) < 3:
    return sendMsg(msgHelp)

  if isAdding:
    return onAddSurvey(
      re1,
      arr,
      groupId,
      creatorId,
      dbAction,
      bot,
      sendMsg
    )

  onVote(
    text,
    dbAction,
    creatorId,
    sendMsg,
    bot,
    msgHelp
  )

def dbTables():
  '''
  db tables to init
  '''
  return dbTablesDef

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
  * for get, singleUser:{'id': xxx}, allUser: None, query: {
    'key': 'xx',
    'value: 'yy'
  }
  """

  print(tableName, action, data)
  sq.prepareDb(dbTables())
  # try:
  id = None
  if 'id' in data:
    id = data['id']
  key = None
  if 'key' in data:
    key = data['key']
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
    if key is None:
      return sq.getOne(tableName, id)
    else:
      return sq.query(tableName, data)

  # except Exception as e:
  #   print(e)
  #   return False

def dbName():
  '''
  return db name
  * set DB_TYPE=custom in .env to activate
  '''
  return 'sqlite3'
