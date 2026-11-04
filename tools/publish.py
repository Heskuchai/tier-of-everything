"""Publish reviewed source and static demos through the user's existing Git login.

Credentials stay in memory. Run without flags for a read-only publication status.
"""
from pathlib import Path
import argparse, json, os, subprocess, urllib.request, urllib.error

ROOT=Path(__file__).resolve().parents[1]
NAME='tier-of-everything'
parser=argparse.ArgumentParser()
parser.add_argument('--publish',action='store_true')
args=parser.parse_args()
env=os.environ.copy();env['GIT_TERMINAL_PROMPT']='0';env['GCM_INTERACTIVE']='never'
credential_result=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\n\n',capture_output=True,text=True,env=env,check=True)
credential=dict(line.split('=',1) for line in credential_result.stdout.splitlines() if '=' in line)
token=credential.get('password')
if not token: raise SystemExit('No GitHub credential is available.')
def api(path,method='GET',payload=None):
    req=urllib.request.Request('https://api.github.com'+path,data=json.dumps(payload).encode() if payload is not None else None,method=method,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','Content-Type':'application/json','User-Agent':'Heskuchai-portfolio-publisher','X-GitHub-Api-Version':'2026-03-10'})
    try:
        with urllib.request.urlopen(req,timeout=40) as response:
            body=response.read()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as error:
        details=error.read().decode('utf-8')
        raise RuntimeError(f'GitHub HTTP {error.code}: {details}') from None
user=api('/user')
if user['login'].lower()!='heskuchai': raise SystemExit('Unexpected GitHub account; publication stopped.')
repo_path='/repos/'+user['login']+'/'+NAME
if args.publish:
    if not (ROOT/'.git').exists():
        try:
            existing=api(repo_path)
        except RuntimeError as error:
            if 'HTTP 404:' not in str(error): raise
            existing=None
        if existing is not None: raise SystemExit('A repository with this name already exists. Review before attaching local source.')
        repo=api('/user/repos','POST',{'name':NAME,'description':'Tier of Everything: a minimal tier-list catalog, personal rankings, search and PNG export.','private':False,'auto_init':False})
        # Persist non-secret repository identity immediately after successful creation.
        (ROOT/'.repository.json').write_text(json.dumps({'full_name':repo['full_name'],'url':repo['html_url'],'clone_url':repo['clone_url']},indent=2),encoding='utf-8')
        subprocess.run(['git','init','-b','main'],cwd=ROOT,check=True)
        subprocess.run(['git','remote','add','origin',repo['clone_url']],cwd=ROOT,check=True)
        subprocess.run(['git','config','user.name',user['login']],cwd=ROOT,check=True)
        subprocess.run(['git','config','user.email',str(user['id'])+'+'+user['login']+'@users.noreply.github.com'],cwd=ROOT,check=True)
    else:
        repo=api(repo_path)
        remote=subprocess.check_output(['git','remote','get-url','origin'],cwd=ROOT,text=True).strip()
        if remote!=repo['clone_url']: raise SystemExit('Repository identity mismatch.')
    subprocess.run(['git','add','.'],cwd=ROOT,check=True)
    changes=subprocess.run(['git','diff','--cached','--quiet'],cwd=ROOT)
    if changes.returncode==1:
        subprocess.run(['git','commit','-m','Launch Tier of Everything catalog and ranking editor'],cwd=ROOT,check=True)
    elif changes.returncode!=0: raise SystemExit('Unable to inspect staged changes.')
    subprocess.run(['git','push','-u','origin','main'],cwd=ROOT,env=env,check=True)
    created_pages=False
    try: pages=api(repo_path+'/pages')
    except RuntimeError as error:
        if 'HTTP 404:' not in str(error): raise
        pages=api(repo_path+'/pages','POST',{'build_type':'workflow'})
        created_pages=True
    if created_pages:
        api(repo_path+'/actions/workflows/pages.yml/dispatches','POST',{'ref':'main'})
    print(json.dumps({'repository':repo['html_url'],'pages_url':pages.get('html_url'),'pages_status':pages.get('status')},ensure_ascii=False))
else:
    repo=api(repo_path);pages=api(repo_path+'/pages')
    runs=api(repo_path+'/actions/workflows/pages.yml/runs?per_page=1')['workflow_runs']
    builds=runs[0] if runs else {}
    print(json.dumps({'repository':repo['html_url'],'pages_url':pages.get('html_url'),'pages_status':pages.get('status'),'build_status':builds.get('status'),'conclusion':builds.get('conclusion'),'commit':builds.get('head_sha'),'run_url':builds.get('html_url')},ensure_ascii=False))
