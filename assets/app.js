
(function(){
  var root=document.documentElement;
  var KEY='gp-theme', saved=localStorage.getItem(KEY);
  if(saved){root.setAttribute('data-theme',saved);}
  else if(matchMedia('(prefers-color-scheme: dark)').matches){root.setAttribute('data-theme','dark');}
  var tb=document.getElementById('themeBtn');
  if(tb)tb.addEventListener('click',function(){
    var cur=root.getAttribute('data-theme')==='dark'?'light':'dark';
    root.setAttribute('data-theme',cur);localStorage.setItem(KEY,cur);
  });
  var mb=document.getElementById('menuBtn'), sb=document.getElementById('sidebar');
  if(mb&&sb)mb.addEventListener('click',function(){sb.classList.toggle('open');});
  var ts=document.getElementById('topSearch');
  if(ts)ts.addEventListener('keydown',function(e){
    if(e.key==='Enter'){
      var q=ts.value.trim(), r=root.getAttribute('data-root')||'';
      location.href=r+'search.html'+(q?('?q='+encodeURIComponent(q)):'');
    }
  });
})();
(function(){
  var box=document.getElementById('q'), out=document.getElementById('hits'), meta=document.getElementById('hitmeta');
  if(!box||!out)return;
  var data=null, root=document.documentElement.getAttribute('data-root')||'';
  function esc(s){return String(s).replace(/[&<>]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;'}[c];});}
  function hl(s,q){
    var i=s.toLowerCase().indexOf(q.toLowerCase());
    if(i<0)return esc(s);
    return esc(s.slice(0,i))+'<mark>'+esc(s.slice(i,i+q.length))+'</mark>'+esc(s.slice(i+q.length));
  }
  function render(q){
    if(!data)return;
    q=(q||'').trim();
    if(!q){out.innerHTML='';if(meta)meta.textContent='输入关键词开始检索，例如「苏晞」「Z-5」「反刷」「价格」「判定」。';return;}
    var terms=q.toLowerCase().split(/\s+/).filter(Boolean), hits=[];
    data.forEach(function(d){
      var hay=(d.t+' '+d.h+' '+d.b).toLowerCase(), score=0;
      for(var i=0;i<terms.length;i++){
        var t=terms[i], idx=hay.indexOf(t);
        if(idx<0){score=-1;break;}
        score += (d.t.toLowerCase().indexOf(t)>=0?8:0) + (d.h.toLowerCase().indexOf(t)>=0?3:0) + 1;
      }
      if(score<0)return;
      var body=d.b, pos=-1;
      for(var j=0;j<terms.length;j++){var k=body.toLowerCase().indexOf(terms[j]);if(k>=0&&(pos<0||k<pos))pos=k;}
      if(pos<0)pos=0;
      hits.push({d:d,s:score,snip:body.slice(Math.max(0,pos-70), Math.max(0,pos-70)+190)});
    });
    hits.sort(function(a,b){return b.s-a.s;});
    if(meta)meta.textContent='找到 '+hits.length+' 条结果';
    out.innerHTML=hits.slice(0,60).map(function(h){
      return '<div class="hit"><h3><a href="'+root+h.d.u+'">'+hl(h.d.t,q.split(/\s+/)[0])+'</a></h3>'+
        '<div class="path">'+esc(h.d.p)+'</div><p>'+esc(h.snip)+'…</p></div>';
    }).join('')||'<p class="hint">没有匹配的条目。</p>';
  }
  fetch(root+'search-index.json').then(function(r){return r.json();}).then(function(j){
    data=j; var q=new URLSearchParams(location.search).get('q')||''; box.value=q; render(q);
  }).catch(function(e){out.innerHTML='<p class="hint">搜索索引加载失败：'+esc(e)+'</p>';});
  box.addEventListener('input',function(){render(box.value);});
})();
