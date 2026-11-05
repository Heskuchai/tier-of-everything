(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory();else root.TierAdmin=factory();})(typeof globalThis!=='undefined'?globalThis:this,function(){
 'use strict';
 const ranks=['S','A','B','C','D','F'],themes=['sand','rose','sage','sky','peach','lavender','butter','mint'];
 const repo='/repos/Heskuchai/tier-of-everything';
 const imageURL=s=>!s||/^media\/[a-zA-Z0-9-]+\.(?:webp|png|jpe?g)$/.test(s)||(()=>{try{const u=new URL(s);return u.protocol==='https:'&&!u.username&&!u.password;}catch{return false;}})();
 function validate(data){
  if(!data||!Array.isArray(data.lists)||!data.lists.length||!Array.isArray(data.categories)||!data.categories.length)throw new Error('Добавь хотя бы один тирлист и категорию.');
  const ids=new Set(),cats=new Set();
  for(const c of data.categories){if(!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(c.id)||!c.name?.trim()||cats.has(c.id))throw new Error('Проверь названия и идентификаторы категорий.');cats.add(c.id);}
  for(const l of data.lists){
   if(!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(l.id)||ids.has(l.id))throw new Error('У тирлистов должны быть разные идентификаторы из латинских букв, цифр и дефисов.');ids.add(l.id);
   if(!l.title?.trim()||l.title.length>85||!l.description?.trim()||!l.criteria?.trim()||!l.icon?.trim())throw new Error(`«${l.title||'Без названия'}»: заполни название, описание, критерий и значок. Название - до 85 символов.`);
   if(!cats.has(l.category)||!themes.includes(l.theme))throw new Error(`«${l.title}»: выбери категорию и цвет.`);
   if(!imageURL(l.image))throw new Error(`«${l.title}»: картинка должна быть HTTPS-ссылкой или загруженным файлом.`);
   if(!Array.isArray(l.items)||!l.items.length||l.items.length>250)throw new Error(`«${l.title}»: нужно от 1 до 250 предметов.`);
   const items=new Set();for(const i of l.items){
    if(!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(i.id)||items.has(i.id))throw new Error(`«${l.title}»: повторяющийся или неверный ID предмета.`);items.add(i.id);
    if(!i.name?.trim()||i.name.length>70||!i.note?.trim()||!i.emoji?.trim()||!ranks.includes(i.tier))throw new Error(`«${l.title}»: заполни названия, пояснения и уровни всех предметов. Название - до 70 символов.`);
    if(!imageURL(i.image))throw new Error(`«${i.name}»: проверь адрес картинки.`);
   }
  }
  return data;
 }
 const encode=s=>{const bytes=new TextEncoder().encode(s);let binary='';for(const b of bytes)binary+=String.fromCharCode(b);return btoa(binary);};
 const decode=s=>new TextDecoder().decode(Uint8Array.from(atob(s.replace(/\s/g,'')),c=>c.charCodeAt(0)));
 const today=()=>{const p=Object.fromEntries(new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/Kyiv',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date()).map(p=>[p.type,p.value]));return `${p.year}-${p.month}-${p.day}`;};
 function safeDraft(d){
  if(!d?.data||!Array.isArray(d.data.lists)||!d.data.lists.length||!Array.isArray(d.data.categories)||!d.data.categories.length||!d.assets||typeof d.assets!=='object'||Array.isArray(d.assets)||!Array.isArray(d.changed))throw new Error('Неверная копия черновика.');
  const id=s=>typeof s==='string'&&/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(s),text=s=>typeof s==='string';
  const seen=new Set();for(const l of d.data.lists){if(!id(l.id)||seen.has(l.id)||!themes.includes(l.theme)||!['title','description','criteria','icon','category','created','updated'].every(k=>text(l[k]))||!imageURL(l.image)||!Array.isArray(l.items)||l.items.length>250||!Array.isArray(l.history))throw new Error('Повреждён тирлист в копии.');seen.add(l.id);const items=new Set();for(const i of l.items){if(!id(i.id)||items.has(i.id)||!['name','emoji','note'].every(k=>text(i[k]))||!ranks.includes(i.tier)||!imageURL(i.image))throw new Error('Повреждён предмет в копии.');items.add(i.id);}if(l.history.some(h=>!text(h.date)||!text(h.text)))throw new Error('Неверная история изменений.');}
  const cats=new Set();for(const c of d.data.categories){if(!id(c.id)||cats.has(c.id)||!text(c.name)||!text(c.icon))throw new Error('Повреждена категория в копии.');cats.add(c.id);}
  for(const [path,content] of Object.entries(d.assets))if(!/^media\/[a-z0-9-]+\.webp$/.test(path)||typeof content!=='string'||!/^[A-Za-z0-9+/]*={0,2}$/.test(content)||content.length>1500000)throw new Error('Неверное изображение в копии.');
  if(!d.changed.every(id)||!(d.baseSha===null||/^[0-9a-f]{40}$/.test(d.baseSha))||typeof d.baseline!=='string')throw new Error('Повреждены сведения о черновике.');
  return {data:d.data,assets:d.assets,changed:d.changed,baseSha:d.baseSha,baseline:d.baseline};
 }
 const clone=data=>JSON.parse(JSON.stringify(data));
 function prepare(data,changed,message,date=today()){
  const result=clone(data);for(const l of result.lists){if(changed.includes(l.id)){l.updated=date;l.history=[{date,text:message||'Обновлено через панель автора.'},...(l.history||[])];}if(!l.created)l.created=date;}
  validate(result);return result;
 }
 function filesFor(data,assets){const paths=new Set(data.lists.flatMap(l=>[l.image,...l.items.map(i=>i.image)]).filter(p=>p?.startsWith('media/')));return Object.entries(assets||{}).filter(([path])=>paths.has(path)).map(([path,content])=>({path,content}));}
 class Publisher{
  constructor(fetcher){this.fetcher=fetcher;this.token='';this.sha=null;}
  disconnect(){this.token='';this.sha=null;}
  async api(path,method='GET',body){
   if(!this.token)throw new Error('Сначала подключи GitHub.');
   const response=await this.fetcher('https://api.github.com'+path,{method,redirect:'error',cache:'no-store',headers:{Authorization:'Bearer '+this.token,Accept:'application/vnd.github+json','Content-Type':'application/json','X-GitHub-Api-Version':'2022-11-28'},...(body?{body:JSON.stringify(body)}:{})});
   if(!response.ok){if(response.status===401)throw new Error('Ключ GitHub недействителен или истёк. Подключись заново.');if(response.status===403)throw new Error('GitHub запретил операцию. Проверь срок ключа и доступ Contents: Read and write к этому репозиторию.');if(response.status===409||response.status===422)throw new Error('Ветка изменилась во время публикации. Черновик сохранён. Загрузи свежую версию и повтори изменения.');throw new Error('GitHub: ошибка '+response.status+'. Черновик сохранён.');}
   return response.status===204?null:response.json();
  }
  async connect(token){this.token=token.trim();try{const user=await this.api('/user');if(user.login?.toLowerCase()!=='heskuchai')throw new Error('Публикация доступна только аккаунту Heskuchai.');const meta=await this.api(repo);if(meta.permissions?.push===false)throw new Error('У ключа нет права записи в этот репозиторий.');const file=await this.api(repo+'/contents/data/tiers.json?ref=main');const data=validate(JSON.parse(decode(file.content)));this.sha=file.sha;return {data,sha:file.sha,login:user.login};}catch(e){this.disconnect();throw e;}}
  async publish(data,assets,baseSha,onProgress=()=>{}){
   validate(data);if(!baseSha)throw new Error('Нет исходной версии. Сначала загрузи актуальный каталог из GitHub.');
   onProgress('Проверяем исходную версию...');const ref=await this.api(repo+'/git/ref/heads/main');const head=ref.object.sha;
   const file=await this.api(repo+'/contents/data/tiers.json?ref='+head);if(file.sha!==baseSha)throw new Error('Каталог уже изменился в GitHub. Черновик сохранён. Скачай его копию перед загрузкой свежей версии.');
   const commit=await this.api(repo+'/git/commits/'+head),tree=[];
   for(const f of filesFor(data,assets)){onProgress('Загружаем изображения...');const blob=await this.api(repo+'/git/blobs','POST',{content:f.content,encoding:'base64'});tree.push({path:f.path,mode:'100644',type:'blob',sha:blob.sha});}
   const blob=await this.api(repo+'/git/blobs','POST',{content:encode(JSON.stringify(data,null,2)+'\n'),encoding:'base64'});tree.push({path:'data/tiers.json',mode:'100644',type:'blob',sha:blob.sha});
   const nextTree=await this.api(repo+'/git/trees','POST',{base_tree:commit.tree.sha,tree});
   const next=await this.api(repo+'/git/commits','POST',{message:'Update tier lists from author panel',tree:nextTree.sha,parents:[head]});
   onProgress('Сохраняем в GitHub...');await this.api(repo+'/git/refs/heads/main','PATCH',{sha:next.sha,force:false});this.sha=blob.sha;return {sha:blob.sha,commit:next.sha};
  }
 }
 return {ranks,themes,imageURL,validate,prepare,filesFor,Publisher,today,clone,encode,decode,safeDraft};
});
