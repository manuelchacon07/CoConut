
import os
from bottle import route,run,get,template,request, static_file, response, redirect, app, debug, abort, error
import psycopg2
import functions
import urllib, hashlib
from beaker.middleware import SessionMiddleware

session_opts = {
    'session.type': 'memory',
    'session.cookie_expires': 600,
    'session.auto': True
}
app = SessionMiddleware(app(), session_opts)

# Login page
@route('/')
def index():
	return template('views/login.tpl')

@route('/login', method='POST')
def login():
 # Request variables
 v_user = request.forms.get('user')
 v_password = request.forms.get('password')
 if v_user == None:
  abort(401, "Sorry, access denied.")
 else:
  sql_query = "SELECT user_user, user_name FROM users WHERE user_user = '%s'" %(v_user)
  datosusuario = functions.test_connection(sql_query, v_user, v_password)
  if datosusuario is not None:
   functions.set('s_user',v_user)
   functions.set('s_password',v_password)
   functions.set('s_name', datosusuario[1])
   redirect('/dashboard')
  else:
   abort(401, "Sorry, access denied.")

# Main page
@route('/dashboard')
def dashboard():
 v_user = functions.get('s_user')
 v_password = functions.get('s_password')
 if v_user == "":
  abort(401, "Sorry, access denied.")
 else:
  v_name = functions.get('s_name')
  selectbackup="select backup_host, host_name, backup_action from backups join hosts on host_ip = backup_host where backup_user = '%s' order by backup_date limit 3;" %(v_user)
  selectbackupusers="select backup_host, host_name, backup_user, to_char(backup_date, 'DD-MM-YYYY') from backups join hosts on host_ip = backup_host order by backup_date limit 5;"
  # sql_select = "select user_name from users where user_user = '%s';" %(v_user)
  backups=functions.selectall(selectbackup, v_user, v_password)
  backupsusers=functions.selectall(selectbackupusers, v_user, v_password)
  gravatar_url = functions.miniavatar(v_user,v_password)
  return template('views/index.tpl', user_user=v_user, user_name=v_name, user_urlimage=gravatar_url, backups=backups, backupsusers=backupsusers)

# Profile path
@route('/profile')
def profile():
 v_user = functions.get('s_user')
 v_password = functions.get('s_password')
 if v_user == "":
  abort(401, "Sorry, access denied.")
 else:
  sql_select="SELECT * FROM USERS WHERE user_user='%s'" %(v_user)
  campos=functions.database_select(sql_select, v_user, v_password)
  gravatar_url = functions.miniavatar(v_user,v_password)
  return template('views/profile.tpl',  user_user=campos[0], user_name=campos[1], user_email=campos[2], user_date=campos[3], user_role=campos[4], user_urlimage=gravatar_url)


# Backups list
@route('/backups', method=['get','post'])
def backups():
 v_user = functions.get('s_user')
 v_password = functions.get('s_password')
 if v_user == "":
  abort(401, "Sorry, access denied.")
 else:
  v_fromdate = request.forms.get('date1')
  print v_fromdate # 2017-12-20
  v_todate = request.forms.get('date2')
  v_host = request.forms.get('host')
  print v_host
  if v_host == "" or v_host == None:
   if v_fromdate == None:
    sql_select="SELECT backup_host, backup_label, backup_description, backup_action, to_char(backup_date, 'DD-MM-YYYY HH24:MI:SS'), backup_check FROM BACKUPS WHERE backup_user='%s'" %(v_user)
   else:
 #  if v_fromdate <= v_todate:
    sql_select="select backup_host, backup_label, backup_description, backup_action, to_char(backup_date, 'DD-MM-YYYY HH24:MI:SS') from backups where backup_date between '%s 00:00:00' and '%s 23:59:59' and backup_user = '%s' order by backup_date desc;" %(v_fromdate, v_todate, v_user)
  else:
   sql_select="select backup_host, backup_label, backup_description, backup_action, to_char(backup_date, 'DD-MM-YYYY HH24:MI:SS') from backups where backup_date between '%s 00:00:00' and '%s 23:59:59' and backup_host = (select host_ip from hostsowners where user_user = '%s' and host_ip = '%s') order by backup_date desc;" %(v_fromdate, v_todate, v_user, v_host)
  campos=functions.selectall(sql_select, v_user, v_password)
  gravatar_url = functions.miniavatar(v_user,v_password)
  return template('views/backups.tpl', backups=campos, user_user=v_user, user_urlimage=gravatar_url)

# New Backup forms
@route('/newbackup')
def newbackup():
 v_user = functions.get('s_user')
 v_password = functions.get('s_password')
 if v_user == "":
  abort(401, "Sorry, access denied.")
 else:
  v_user = functions.get('s_user')
  v_password = functions.get('s_password')
  sql_select="select host_ip, host_name from hosts where host_ip in (select host_ip from hostsowners where user_user = '%s');" %(v_user)
  campos=functions.selectall(sql_select, v_user, v_password)
  gravatar_url = functions.miniavatar(v_user,v_password)
  return template('views/newbackup.tpl', user_user=v_user, hosts=campos, user_urlimage=gravatar_url)

# Insert new backups
@route('/insert', method='POST')
def insertbackup():
 v_user = functions.get('s_user')
 v_password = functions.get('s_password')
 if v_user == "":
  abort(401, "Sorry, access denied.")
 else:
  v_label = request.forms.get('label')
  v_ip = request.forms.get('ip')
  v_desc = request.forms.get('desc')
  sql_insert="insert into backups (backup_user, backup_host, backup_label, backup_description, backup_action) values ('%s','%s','%s','%s','%s');" %(v_user, v_ip, v_label, v_desc, 'Manual')
  functions.database_insert(sql_insert, v_user, v_password)
  redirect('/backups')

# Do logout
@route('/logout')
def logout():
 functions.delete()
 redirect('/')

# Static files
@route('/static/<filepath:path>')
def server_static(filepath):
	return static_file(filepath, root='static')

# error handlers
@error(404)
def error404(error):
    return template('views/error/404.tpl')
@error(401)
def error401(error):
    return template('views/error/401.tpl')

debug(True)
run(app=app, host = '0.0.0.0', port = 8080)
