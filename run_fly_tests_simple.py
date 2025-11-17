import requests, uuid, os, sys
BASE = os.getenv('BASE_URL', 'https://bizeng-server.fly.dev').rstrip('/')
headers = {'Content-Type':'application/json'}

def call_get(path):
    url = BASE + path
    try:
        r = requests.get(url, timeout=20)
        print(path, r.status_code)
        try:
            print(r.json())
        except Exception:
            print(r.text[:1000])
        return r
    except Exception as e:
        print(path, 'ERROR', e)
        return None

def call_post(path, json=None, hdrs=None):
    url = BASE + path
    h = hdrs or headers
    try:
        r = requests.post(url, json=json, headers=h, timeout=30)
        print(path, r.status_code)
        try:
            print(r.json())
        except Exception:
            print(r.text[:1000])
        return r
    except Exception as e:
        print(path, 'ERROR', e)
        return None

print('BASE:', BASE)

# Health & version
call_get('/health')
call_get('/version')

# Chat & Ask
call_post('/chat', json={"messages":[{"role":"user","content":"Hello, how are you?"}]})
call_post('/ask', json={"query":"What are the stages of a business meeting?","k":3})

# Pronunciation test
call_get('/pronunciation/test')

# Roleplay
res = call_get('/roleplay/scenarios')
session_id = None
if res and res.status_code==200:
    data=res.json()
    sc = data.get('scenarios')
    if sc and isinstance(sc, list) and len(sc)>0:
        sid = sc[0].get('id') if isinstance(sc[0], dict) else None
        if sid:
            r = call_post('/roleplay/start', json={'scenario_id':sid,'student_name':'AutoTester'})
            if r and r.status_code==200:
                session_id = r.json().get('session_id')
                call_post('/roleplay/turn', json={'session_id':session_id,'message':'Hello, I am testing.'})

# Auth flows
uniq = uuid.uuid4().hex[:8]
email = f'ci_test+{uniq}@example.com'
print('\nTesting auth with', email)
reg = call_post('/auth/register', json={'email':email,'password':'Test12345!','display_name':'CI Test'})
access = None; refresh = None
if reg and reg.status_code in (200,201):
    j=reg.json(); access=j.get('access_token'); refresh=j.get('refresh_token')
else:
    login = call_post('/auth/login', json={'email':email,'password':'Test12345!'})
    if login and login.status_code==200:
        j=login.json(); access=j.get('access_token'); refresh=j.get('refresh_token')

if refresh:
    rr = call_post('/auth/refresh', json={'refresh_token':refresh})
    if rr and rr.status_code==200:
        j=rr.json(); access=j.get('access_token'); refresh=j.get('refresh_token')

# Tracking (requires auth)
if access:
    hdr = {'Content-Type':'application/json','Authorization':f'Bearer {access}'}
    st = call_post('/tracking/attempts', json={'exercise_type':'roleplay','exercise_id':session_id or 'manual','extra_metadata':{}}, hdrs=hdr)
    attempt_id=None
    if st and st.status_code in (200,201):
        attempt_id = st.json().get('id')
    if attempt_id:
        r = requests.patch(BASE+f'/tracking/attempts/{attempt_id}', json={'status':'completed','score':0.95,'duration_seconds':30}, headers=hdr, timeout=20)
        print('/tracking/attempts/{id}', r.status_code)
        try:
            print(r.json())
        except:
            print(r.text[:800])
    ev = call_post('/tracking/events', json={'event_type':'opened_chat','feature':'chat','extra_metadata':{'screen':'chat'}}, hdrs=hdr)
else:
    print('No access token -> skipping tracking tests')

print('\nDONE')

