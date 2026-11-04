(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory();else root.TierCore=factory();})(typeof globalThis!=='undefined'?globalThis:this,function(){
 'use strict';
 const ranks=['S','A','B','C','D','F'];
 const normalize=s=>String(s??'').toLocaleLowerCase('ru').replace(/ё/g,'е').trim();
 function search(lists,{q='',categories=[],savedOnly=false,saved=[],sort='updated'}={}){
  const words=normalize(q).split(/\s+/).filter(Boolean);
  return lists.filter(l=>(!categories.length||categories.includes(l.category))&&(!savedOnly||saved.includes(l.id))&&words.every(w=>normalize([l.title,l.description,...l.items.map(i=>i.name)].join(' ')).includes(w))).sort((a,b)=>sort==='title'?a.title.localeCompare(b.title,'ru'):String(b[sort==='new'?'created':'updated']).localeCompare(String(a[sort==='new'?'created':'updated']))||a.title.localeCompare(b.title,'ru'));
 }
 const author=l=>Object.fromEntries(l.items.map(i=>[i.id,i.tier]));
 function reconcile(list,stored){const map=author(list);if(stored&&typeof stored==='object'&&!Array.isArray(stored))for(const item of list.items)if(ranks.includes(stored[item.id]))map[item.id]=stored[item.id];return map;}
 function move(list,map,itemId,tier){if(!list.items.some(i=>i.id===itemId)||!ranks.includes(tier))throw new Error('Invalid item or tier');return {...reconcile(list,map),[itemId]:tier};}
 function parseRoute(hash){const raw=String(hash||'#/').replace(/^#/,'');const [path,query='']=raw.split('?');const params=new URLSearchParams(query);const categories=(params.get('cat')||'').split(',').filter(Boolean);return {path:path||'/',q:params.get('q')||'',categories,sort:['updated','new','title'].includes(params.get('sort'))?params.get('sort'):'updated'};}
 function route(path,{q='',categories=[],sort='updated'}={}){const p=new URLSearchParams();if(q)p.set('q',q);if(categories.length)p.set('cat',categories.join(','));if(sort!=='updated')p.set('sort',sort);return '#'+path+(p.size?'?'+p.toString():'');}
 return {ranks,normalize,search,author,reconcile,move,parseRoute,route};
});
