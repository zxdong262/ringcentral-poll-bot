try:
  import sqlite3
except:
  pass
import os
import json
import pydash as _

fileName = 'sqlite3.db'
try:
  fileName = os.environ['SQLITE_DB_NAME']
except:
  pass

tbs = []

def createConnection():
  conn = sqlite3.connect(fileName)
  cur = conn.cursor()
  return cur, conn


def tableExist(tableName):
  sql = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{tableName}';"
  cur, conn = createConnection()
  res = cur.execute(sql)
  f = res.fetchone()
  conn.close()
  return not f is None

def prepareDb(tables):
  global tbs
  tbs = tables
  for table in tables:
    name = table['name']
    if tableExist(name):
      continue
    schemas = table['schemas']
    st = f'create table {name} ('
    i = 0
    prim = None
    for s in schemas:
      n = s['name']
      t = s['type']
      if prim is None and 'primary' in s and s['primary']:
        prim = n
      tp = t == 'string' or t == 'json'
      pre = '' if i == 0 else ','
      st = st + f'{pre}{n} {tp}'
      i = i + 1
    st = st + f', PRIMARY KEY ({prim}))'
    cur, conn = createConnection()
    cur.execute(st)
    conn.commit()
    conn.close()

def resultMapper(res, tableName):
  obj = {}
  dbDef = _.collections.find(tbs, lambda x: x['name'] == tableName)
  opts = dbDef['schemas']
  i = 0
  for opt in opts:
    tp = opt['type']
    nm = opt['name']
    v = res[i]
    obj[nm] = json.loads(v) if not tp == 'string' else v
    i = i + 1
  return obj

def getOne(tableName, id):
  cur, conn = createConnection()
  st = f"select * from {tableName} where id='{id}';"
  cur.execute(st)
  res = cur.fetchone()
  conn.close()
  if not _.predicates.is_tuple(res):
    return False
  return resultMapper(res, tableName)

def query(tableName, query):
  '''
  single query
  '''
  cur, conn = createConnection()
  key = query['key']
  value = query['value']
  st = f"select * from {tableName} where {key}='{value}';"
  cur.execute(st)
  reses = cur.fetchall()
  conn.close()
  final = []
  for res in reses:
    final.append(
      resultMapper(res, tableName)
    )
  return final

def delOne(tableName, id):
  cur, conn = createConnection()
  st = f"DELETE FROM {tableName} WHERE id='{id}';"
  cur.execute(st)
  conn.commit()
  conn.close()

def updateOne(tableName, id, update):
  keys = update.keys()
  i = 0
  ss = ''
  for k in keys:
    pre = '' if i == 0 else ','
    v = json.dumps(update[k])
    ss = ss + f"{pre}{k} = '{v}'"
    i = i + 1

  cur, conn = createConnection()
  st = f"update {tableName} set {ss} WHERE id='{id}';"
  cur.execute(st)
  conn.commit()
  conn.close()

def addOne(tableName, item):
  keys = item.keys()
  i = 0
  cs = ''
  vs = ''
  defs = _.collections.find(
    tbs,
    lambda x: x['name'] == tableName
  )
  schemas = defs['schemas']
  if defs is None:
    return False
  for k in keys:
    pre = '' if i == 0 else ', '
    schema = _.collections.find(
      schemas,
      lambda x: x['name'] == k
    )
    if schema is None:
      continue
    v = json.dumps(item[k]) if schema['type'] == 'json' else item[k]
    cs = cs + f"{pre}'{k}'"
    vs = vs + f"{pre}'{v}'"
    i = i + 1

  st = f"insert into {tableName} ({cs}) values ({vs});"
  cur, conn = createConnection()
  cur.execute(st)
  conn.commit()
  conn.close()
