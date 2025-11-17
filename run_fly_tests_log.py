import requests, uuid, os, time
BASE = os.getenv('BASE_URL', 'https://bizeng-server.fly.dev').rstrip('/')
logfile = 'fly_test_results.txt'
with open(logfile, 'w', encoding='utf-8') as f:
    def log(msg=''):
        print(msg)
        f.write(msg + '\n')
    def try_get(path):
        url = BASE + path
        try:
            r = requests.get(url, timeout=20)
            log(f'GET {path} -> {r.status_code}')
            try:
                log(str(r.json()))
            except Exception:
                log(r.text[:1000])
            return r
        except Exception as e:
            log(f'GET {path} ERROR: {e}')
            return None
    def try_post(path, json=None, hdrs=None):
        url = BASE + path
        h = hdrs or {'Content-Type':'application/json'}
        try:
            r = requests.post(url, json=json, headers=h, timeout=30)
            log(f'POST {path} -> {r.status_code}')
            try:
                log(str(r.json()))
            except Exception:
                log(r.text[:1000])
            return r
        except Exception as e:
            log(f'POST {path} ERROR: {e}')
            return None

    log('BASE: ' + BASE)
    log('\n-- health & version --')
    try_get('/health')
    try_get('/version')

    log('\n-- chat & ask --')
    try_post('/chat', json={"messages":[{"role":"user","content":"Hello, how are you?"}]})
    try_post('/ask', json={"query":"What are the stages of a business meeting?","k":3})

    log('\n-- pronunciation test --')
    try_get('/pronunciation/test')

    log('\n-- roleplay --')
    res = try_get('/roleplay/scenarios')
    session_id = None
    if res and res.status_code==200:
        data=res.json(); sc = data.get('scenarios')
        if sc and isinstance(sc, list) and len(sc)>0:
            sid = sc[0].get('id') if isinstance(sc[0], dict) else None
            if sid:
                r = try_post('/roleplay/start', json={'scenario_id':sid,'student_name':'AutoTester'})
                if r and r.status_code==200:
                    session_id = r.json().get('session_id')
                    try_post('/roleplay/turn', json={'session_id':session_id,'message':'Hi, test turn.'})

    log('\n-- auth flows --')
    uniq = uuid.uuid4().hex[:8]
    email = f'ci_test+{uniq}@example.com'
    password = 'Test12345!'
    log('registering ' + email)
    reg = try_post('/auth/register', json={'email':email,'password':password,'display_name':'CI Test'})
    access=None; refresh=None
    if reg and reg.status_code in (200,201):
        j=reg.json(); access=j.get('access_token'); refresh=j.get('refresh_token')
    else:
        login = try_post('/auth/login', json={'email':email,'password':password})
        if login and login.status_code==200:
            j=login.json(); access=j.get('access_token'); refresh=j.get('refresh_token')
    if refresh:
        rr = try_post('/auth/refresh', json={'refresh_token':refresh})
        if rr and rr.status_code==200:
            j=rr.json(); access=j.get('access_token'); refresh=j.get('refresh_token')

    log('\n-- tracking --')
    if access:
        hdr = {'Content-Type':'application/json','Authorization':f'Bearer {access}'}
        st = try_post('/tracking/attempts', json={'exercise_type':'roleplay','exercise_id':session_id or 'manual','extra_metadata':{}}, hdrs=hdr)
        attempt_id=None
        if st and st.status_code in (200,201):
            attempt_id = st.json().get('id')
        if attempt_id:
            time.sleep(1)
            pa = requests.patch(BASE+f'/tracking/attempts/{attempt_id}', json={'status':'completed','score':0.9,'duration_seconds':45}, headers=hdr, timeout=15)
            log(f'PATCH /tracking/attempts/{attempt_id} -> {pa.status_code}')
            try:
                log(str(pa.json()))
            except Exception:
                log(pa.text[:800])
        ev = try_post('/tracking/events', json={'event_type':'opened_chat','feature':'chat','extra_metadata':{'screen':'chat'}}, hdrs=hdr)
    else:
        log('No access token; skipping tracking tests')

    log('\nDONE')

