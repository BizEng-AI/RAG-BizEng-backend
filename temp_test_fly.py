import requests, uuid, time, sys, os
BASE = os.getenv('BASE_URL', 'https://bizeng-server.fly.dev')
HEADERS_JSON = {'Content-Type': 'application/json'}

def try_get(path):
    url = BASE.rstrip('/') + path
    try:
        r = requests.get(url, timeout=15)
        print(path, '->', r.status_code)
        try:
            print(r.json())
        except Exception:
            print(r.text[:800])
    except Exception as e:
        print(path, 'ERROR', e)

def try_post(path, json=None, headers=None):
    url = BASE.rstrip('/') + path
    h = headers or HEADERS_JSON
    try:
        r = requests.post(url, json=json, headers=h, timeout=30)
        print(path, '->', r.status_code)
        try:
            print(r.json())
        except Exception:
            print(r.text[:800])
        return r
    except Exception as e:
        print(path, 'ERROR', e)
        return None

print('BASE =', BASE)

# health and version
try_get('/health')
try_get('/version')

# chat and ask (no auth required but recommended)
print('\n== chat & ask ==')
try_post('/chat', json={'messages':[{'role':'user','content':'Hello, how do I open a meeting politely?'}]})
try_post('/ask', json={'query':'What are the stages of a business meeting?','k':5})

# pronunciation test
try_get('/pronunciation/test')

# roleplay scenarios and start/turn
print('\n== roleplay ==')
res = try_post('/roleplay/start', json={'scenario_id':'job_interview','student_name':'CI Tester'})
session_id = None
if res and res.status_code == 200:
    try:
        session_id = res.json().get('session_id')
    except Exception:
        session_id = None

if session_id:
    try_post('/roleplay/turn', json={'session_id':session_id,'message':'Hello, I am ready to practice.'})

# auth register/login/refresh
print('\n== auth ==')
uniq = uuid.uuid4().hex[:8]
email = f'ci_test+{uniq}@example.com'
password = 'Test12345!'
print('registering', email)
reg = try_post('/auth/register', json={'email':email,'password':password,'display_name':'CI Test'})
access=None; refresh=None
if reg and reg.status_code in (200,201):
    data = reg.json()
    access = data.get('access_token')
    refresh = data.get('refresh_token')
else:
    # try login
    login = try_post('/auth/login', json={'email':email,'password':password})
    if login and login.status_code==200:
        dd=login.json(); access=dd.get('access_token'); refresh=dd.get('refresh_token')

if refresh:
    rr = try_post('/auth/refresh', json={'refresh_token':refresh})
    if rr and rr.status_code==200:
        dd=rr.json(); access=dd.get('access_token'); refresh=dd.get('refresh_token')

# tracking endpoints (need auth)
print('\n== tracking ==')
if access:
    hdr = {'Content-Type':'application/json','Authorization':f'Bearer {access}'}
    st = try_post('/tracking/attempts', json={'exercise_type':'roleplay','exercise_id':session_id or 'manual','extra_metadata':{}}, headers=hdr)
    attempt_id = None
    if st and st.status_code in (200,201):
        attempt_id = st.json().get('id')
    if attempt_id:
        time.sleep(1)
        pa = requests.patch(BASE.rstrip('/') + f'/tracking/attempts/{attempt_id}', json={'status':'completed','score':0.9,'duration_seconds':45}, headers=hdr, timeout=15)
        print('/tracking/attempts/{id} ->', pa.status_code)
        try:
            print(pa.json())
        except Exception:
            print(pa.text[:400])
    ev = try_post('/tracking/events', json={'event_type':'opened_chat','feature':'chat','extra_metadata':{'screen':'chat'}}, headers=hdr)
else:
    print('No auth tokens available; skipping auth-required tracking tests')

print('\nDONE')

