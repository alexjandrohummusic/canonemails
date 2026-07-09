let TOKEN = localStorage.getItem("lx_token") || "";
let CID = null, curTemplate = null, tplKind = "tsl";
const $ = id => document.getElementById(id);
async function api(path, opts = {}) {
  opts.headers = Object.assign({ "Content-Type": "application/json" }, opts.headers || {},
    TOKEN ? { Authorization: "Bearer " + TOKEN } : {});
  const r = await fetch(path, opts);
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw data;
  return data;
}
function show(l){ $("authView").classList.toggle("hidden", l); $("app").classList.toggle("hidden", !l); }
function tab(id, ev){
  document.querySelectorAll(".tabview").forEach(v => v.classList.add("hidden"));
  $(id).classList.remove("hidden");
  document.querySelectorAll(".tabs button").forEach(b => b.classList.remove("on"));
  if (ev) ev.target.classList.add("on");
  if (id === "datos") loadCatalog(); if (id === "tpl") loadTpls();
}
async function login(){
  try { const d = await api("/api/auth/login", { method:"POST",
    body: JSON.stringify({ email:$("aemail").value, password:$("apass").value }) });
    TOKEN = d.token; localStorage.setItem("lx_token", TOKEN); boot(); }
  catch(e){ $("autherr").textContent = e.detail || "Credenciales inválidas"; }
}
function logout(){ TOKEN=""; localStorage.removeItem("lx_token"); show(false); }
async function boot(){
  try {
    const me = await api("/api/account"); show(true);
    $("who").textContent = me.email + (me.subscription_status!=="active" ? " · suscripción inactiva":"");
    $("p_fromname").value = me.from_name||""; $("p_fromemail").value = me.from_email||"";
    curTemplate = me.template;
    $("st_resend").textContent = me.has_resend ? "conectado":"pendiente";
    await renderSetup();
  } catch { show(false); }
}
async function renderSetup(){
  let s={}; try { s = await api("/api/data/status"); } catch {}
  const chip=(ok,l)=>`<span class="pill" style="background:${ok?'#d6f0d8':'#fcefcf'};color:${ok?'#1c5a24':'#8a5a04'}">${ok?'✓':'•'} ${l}</span>`;
  $("setupStrip").innerHTML = "<b style='color:#0B2545'>Progreso:</b> " +
    chip(s.has_sales,"Ventas")+" "+chip(s.catalog_valid,"Catálogo"+(s.principales?` (${s.principales} principales)`:""))+" "+
    chip(s.has_resend,"Resend")+" "+chip(!!s.from_email,"Remitente");
}
async function uploadSales(){
  const f=$("salesfile").files[0]; if(!f) return alert("Elige tu archivo de ventas");
  $("salesout").innerHTML="Subiendo…";
  const fd=new FormData(); fd.append("file",f);
  try{
    const r=await fetch("/api/data/sales",{method:"POST",headers:{Authorization:"Bearer "+TOKEN},body:fd});
    const d=await r.json(); if(!r.ok) throw d;
    $("salesout").innerHTML=`<div class="note"><span class="ok">✓ ${d.product_count} productos detectados.</span> ` +
      (d.catalog_created?"Creamos tu plantilla de catálogo — complétala abajo.":"Catálogo ya existente, revísalo abajo.")+"</div>";
    loadCatalog(); renderSetup();
  }catch(e){ $("salesout").innerHTML='<span class="bad">'+(e.detail||"Error al subir")+"</span>"; }
}
async function loadCatalog(){
  const r=await fetch("/api/data/catalog",{headers:{Authorization:"Bearer "+TOKEN}});
  if(r.ok) $("cf_catalogo").value = await r.text();
}
async function downloadCatalog(){
  const r=await fetch("/api/data/catalog",{headers:{Authorization:"Bearer "+TOKEN}});
  const txt=await r.text(); const blob=new Blob([txt],{type:"application/json"});
  const a=document.createElement("a"); a.href=URL.createObjectURL(blob); a.download="catalogo.json"; a.click();
}
function loadCatFile(){
  const f=$("catfile").files[0]; if(!f) return;
  const rd=new FileReader(); rd.onload=()=>{ $("cf_catalogo").value=rd.result; }; rd.readAsText(f);
}
async function saveCatalog(){
  $("catval").innerHTML="Validando…";
  try{
    const v=await api("/api/data/catalog",{method:"POST",body:JSON.stringify({content:$("cf_catalogo").value})});
    let html="";
    if(v.ok) html=`<div class="note"><span class="ok">✓ Catálogo guardado.</span> ${v.productos} productos · ${v.principales} principales. Afinidad calculada automáticamente.</div>`;
    else{
      const probs=[]; if(v.productos===0) probs.push("catálogo vacío");
      if(v.sin_categoria?.length) probs.push("sin categoría: "+v.sin_categoria.join(", "));
      html=`<div class="note" style="border-color:#F0A202"><span style="color:#8a5a04">Guardado, pero revisa: ${probs.join(" · ")}</span></div>`;
    }
    if(v.principales_sin_landing?.length) html+=`<div class="muted">Principales sin link de landing: ${v.principales_sin_landing.join(", ")}</div>`;
    $("catval").innerHTML=html; renderSetup();
  }catch(e){ $("catval").innerHTML='<div class="note" style="border-color:#C1272D"><span class="bad">'+(e.detail||"JSON inválido")+"</span></div>"; }
}
async function saveTokens(){
  if($("t_resend").value) await api("/api/account/tokens",{method:"PUT",body:JSON.stringify({resend_token:$("t_resend").value})});
  $("tokmsg").textContent="Guardado ✓"; $("t_resend").value=""; boot();
}
async function saveProfile(){
  await api("/api/account",{method:"PUT",body:JSON.stringify({from_name:$("p_fromname").value,from_email:$("p_fromemail").value})});
  $("profmsg").textContent="Remitente guardado ✓"; renderSetup();
}
async function checkDom(){
  $("domout").innerHTML="Consultando…";
  try{ const d=await api("/api/domain/check?domain="+encodeURIComponent($("dom").value));
    const b=v=>v?'<span class="ok">OK</span>':'<span class="bad">falta</span>';
    $("domout").innerHTML=`<p>SPF ${b(d.spf)} · DKIM ${b(d.dkim)} · MX ${b(d.mx)} · DMARC ${b(d.dmarc)} — `+
      (d.verified?'<span class="ok">Verificado</span>':'<span class="bad">Aún no (propagación hasta 24 h)</span>')+"</p>"; }
  catch{ $("domout").innerHTML='<span class="bad">Error</span>'; }
}
async function gen(){
  $("genout").innerHTML="Generando…";
  const fd=new FormData(); fd.append("mode",$("mode").value);
  try{
    const r=await fetch("/api/campaigns/generate",{method:"POST",headers:{Authorization:"Bearer "+TOKEN},body:fd});
    const d=await r.json(); if(!r.ok) throw d;
    CID=d.campaign_id; const rep=d.report;
    $("genout").innerHTML=`<div class="note">Campaña #${CID} · <b>${rep.bloques} correos</b> · `+
      Object.entries(rep.distribucion_modo).map(([k,v])=>`<span class="pill">${k}: ${v}</span>`).join(" ")+
      (rep.warn_desconocidos.length?`<br><span class="muted">Productos del archivo no reconocidos: ${rep.warn_desconocidos.length}</span>`:"")+`</div>`;
    if(rep.bloques===0){ $("genout").innerHTML+='<div class="note" style="border-color:#F0A202"><span style="color:#8a5a04">0 correos: revisa tu catálogo y que los nombres coincidan con el archivo.</span></div>'; return; }
    $("previewCard").classList.remove("hidden"); loadPreview();
  }catch(e){
    const msg=e.detail?.detalle?"Faltan categorías en el catálogo.":(typeof e.detail==="string"?e.detail:"Error al generar");
    $("genout").innerHTML='<span class="bad">'+msg+"</span>";
  }
}
async function loadPreview(){
  const d=await api("/api/campaigns/"+CID+"/preview");
  $("previews").innerHTML=d.previews.map(p=>
    `<div style="margin-bottom:10px"><span class="pill">${p.type}</span> <b>${p.email}</b><br>`+
    `<span class="muted">Asunto: ${p.asunto}</span><iframe srcdoc="${p.html.replace(/"/g,'&quot;')}"></iframe></div>`).join("");
}
async function send(){
  $("sendout").innerHTML="Encolando…";
  try{ await api("/api/campaigns/"+CID+"/send",{method:"POST"}); $("sendout").innerHTML='<span class="ok">Envío iniciado.</span> '; refreshStatus(); }
  catch(e){ $("sendout").innerHTML='<span class="bad">'+(e.detail||"Error")+"</span>"; }
}
async function refreshStatus(){
  const d=await api("/api/campaigns/"+CID);
  $("sendout").innerHTML=`<div class="note">Estado: <b>${d.status}</b> · enviados ${d.sent}/${d.total} · fallidos ${d.failed}</div>`;
}
async function loadTpls(){
  const list=await api("/api/templates");
  $("tpllist").innerHTML=list.map(t=>`<span class="tpl ${t.actual?'on':''}" onclick="pickTpl('${t.id}')" id="tpl_${t.id}">${t.nombre}</span>`).join("");
  curTemplate=(list.find(t=>t.actual)||list[0]).id; loadTplPrev();
}
async function pickTpl(id){
  curTemplate=id; await api("/api/account",{method:"PUT",body:JSON.stringify({template:id})});
  document.querySelectorAll(".tpl").forEach(e=>e.classList.remove("on")); $("tpl_"+id).classList.add("on"); loadTplPrev();
}
async function loadTplPrev(){
  if(!curTemplate) return;
  const d=await api(`/api/templates/${curTemplate}/preview?kind=${tplKind}`); $("tplframe").srcdoc=d.html;
}
boot();
