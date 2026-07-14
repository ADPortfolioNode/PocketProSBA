// app.js
// HAL RAG Frontend Demo — complete client-side logic
// - KB ingestion (upload / paste / chunking)
// - Simple retrieval using TF vectors + cosine similarity
// - Local "mock" generator for demo responses
// - Example remote API call pattern (commented / safe)
// - TTS and STT support

const CHUNK_LEN = 600; // characters per chunk for simple chunking
const STOPWORDS = new Set([
  "the","and","a","an","of","to","is","in","it","you","that","i","for","on","with","as","are","this","was","but","be","by","or","not"
]);

/* -------------------------
   DOM references
   ------------------------- */
const fileInput = document.getElementById('fileInput');
const pasteBtn = document.getElementById('pasteBtn');
const kbText = document.getElementById('kbText');
const kbList = document.getElementById('kbList');
const docCount = document.getElementById('docCount');
const chunkCount = document.getElementById('chunkCount');
const clearKb = document.getElementById('clearKb');

const queryInput = document.getElementById('queryInput');
const askBtn = document.getElementById('askBtn');
const responseDiv = document.getElementById('response');
const sourcesDiv = document.getElementById('sources');
const topKInput = document.getElementById('topK');
const speakBtn = document.getElementById('speakBtn');
const micBtn = document.getElementById('micBtn');
const useRemote = document.getElementById('useRemote');
const modeSelect = document.getElementById('modeSelect');

const halEye = document.getElementById('halEye');

// Status indicator elements
const statusIndicator = document.getElementById('statusIndicator');
const statusLight = document.getElementById('statusLight');
const statusText = document.getElementById('statusText');

// Function to update status indicator
function updateStatusIndicator(status) {
  switch(status) {
    case 'connected':
      statusLight.className = 'status-light connected';
      statusText.textContent = 'Connected';
      break;
    case 'connecting':
      statusLight.className = 'status-light connecting';
      statusText.textContent = 'Connecting...';
      break;
    case 'disconnected':
    default:
      statusLight.className = 'status-light disconnected';
      statusText.textContent = 'Disconnected';
      break;
  }
}

// Initial status
updateStatusIndicator('connecting');

// Periodic health check to backend
async function checkBackendHealth() {
  updateStatusIndicator('connecting');
  try {
    const res = await fetch('/api/health', { cache: 'no-store' });
    if (res.ok) {
      updateStatusIndicator('connected');
    } else {
      updateStatusIndicator('disconnected');
    }
  } catch (e) {
    updateStatusIndicator('disconnected');
  }
}

// Check backend health every 10 seconds
setInterval(checkBackendHealth, 10000);

// Initial check on page load
checkBackendHealth();

/* -------------------------
   In-memory KB
   ------------------------- */
let docs = [];     // {id, title, text}
let chunks = [];   // {docId, text, vec}

/* -------------------------
   Utilities: simple tokenizer & term-frequency vector
   ------------------------- */
function tokenize(text){
  return text
    .toLowerCase()
    .replace(/[\p{P}\p{S}]/gu, ' ')
    .split(/\s+/)
    .filter(t => t && !STOPWORDS.has(t));
}

function tfVector(tokens){
  const v = Object.create(null);
  for(const t of tokens){
    v[t] = (v[t] || 0) + 1;
  }
  // optionally normalize by length
  const len = tokens.length || 1;
  for(const k of Object.keys(v)) v[k] = v[k] / len;
  return v;
}

function dot(a,b){
  let sum = 0;
  for(const k of Object.keys(a)){
    if(b[k]) sum += a[k]*b[k];
  }
  return sum;
}

function vecNorm(a){
  let s=0;
  for(const k of Object.keys(a)) s += a[k]*a[k];
  return Math.sqrt(s);
}

function cosine(a,b){
  const den = vecNorm(a)*vecNorm(b);
  if(den===0) return 0;
  return dot(a,b) / den;
}

/* -------------------------
   KB ingestion & chunking
   ------------------------- */
function chunkText(text, docId){
  // naive chunking by characters with overlap
  const chunksLocal = [];
  const overlap = 120;
  let i = 0;
  while(i < text.length){
    const chunk = text.slice(i, i + CHUNK_LEN);
    chunksLocal.push({ docId, text: chunk });
    i += CHUNK_LEN - overlap;
  }
  return chunksLocal;
}

function addDocument(title, text){
  const id = 'doc_' + (docs.length + 1);
  docs.push({id, title, text});
  const newChunks = chunkText(text, id).map(c=>{
    const tokens = tokenize(c.text);
    const vec = tfVector(tokens);
    return { docId: id, text: c.text, vec, title };
  });
  chunks.push(...newChunks);
  renderKb();
}

function renderKb(){
  kbList.innerHTML = '';
  for(const d of docs){
    const el = document.createElement('div');
    el.className = 'kb-item';
    el.textContent = `${d.title} — ${d.text.length} chars`;
    kbList.appendChild(el);
  }
  docCount.textContent = docs.length;
  chunkCount.textContent = chunks.length;
}

/* -------------------------
   File / paste handlers
   ------------------------- */
fileInput.addEventListener('change', async (e)=>{
  const files = Array.from(e.target.files || []);
  for(const f of files){
    if(f.type === 'application/json' || f.name.endsWith('.json')){
      try{
        const txt = await f.text();
        const json = JSON.parse(txt);
        // if array, ingest entries
        if(Array.isArray(json)){
          json.forEach((item, idx) => {
            const title = item.title || `${f.name}#${idx+1}`;
            const text = (item.text || item.content || JSON.stringify(item));
            addDocument(title, text);
          });
        } else {
          const text = json.text || json.content || JSON.stringify(json);
          addDocument(f.name, text);
        }
      }catch(err){
        // fallback: treat file as text
        const text = await f.text();
        addDocument(f.name, text);
      }
    } else {
      const text = await f.text();
      addDocument(f.name, text);
    }
  }
  fileInput.value = '';
});

pasteBtn.addEventListener('click', ()=>{
  const t = kbText.value.trim();
  if(!t) {
    alert('Paste or type text into the KB textarea first.');
    return;
  }
  addDocument('Pasted ' + (docs.length+1), t);
  kbText.value = '';
});

clearKb.addEventListener('click', ()=>{
  if(!confirm('Clear all documents from the knowledge base?')) return;
  docs = []; chunks = [];
  renderKb();
});

/* -------------------------
   Retrieval: pick top-k chunks for a query
   ------------------------- */
function retrieve(query, k=3){
  if(chunks.length===0) return [];
  const qTokens = tokenize(query);
  const qVec = tfVector(qTokens);
  const scored = chunks.map(c => ({...c, score: cosine(qVec, c.vec)}));
  scored.sort((a,b)=> b.score - a.score);
  const picked = scored.slice(0, k).filter(s=>s.score>0);
  return picked;
}

/* -------------------------
   Mock local generator (deterministic)
   - Builds a short answer by combining top contexts and template
   ------------------------- */
function mockGenerate(query, contextChunks){
  // Very simple heuristic "generator" for demo purposes
  if(contextChunks.length === 0){
    return `I'm sorry. I don't have information about that in my knowledge base. Try uploading documents or pasting relevant text.`;
  }
  const ctx = contextChunks.map((c,i)=>`[${i+1}] ${c.text.slice(0,250).replace(/\s+/g,' ')}...`).join('\n\n');
  const answer = `Processing query: "${query}"\n\nContext (top ${contextChunks.length}):\n${ctx}\n\nHAL (local demo): Based on the retrieved documents, here is a summary answer.\n\n- Summary: ${summarizeText(contextChunks.map(c=>c.text).join(' '))}\n\n(Sources: ${[...new Set(contextChunks.map(c=>c.docId))].join(', ')})`;
  return answer;
}

function summarizeText(long){
  // crude summarizer: pick the sentence with most matching words to the text
  const sentences = long.split(/(?<=[.!?])\s+/).filter(s=>s.trim());
  if(!sentences.length) return long.slice(0,200) + '...';
  // score sentences by token overlap
  const tokens = tokenize(long);
  const freq = {};
  for(const t of tokens) freq[t] = (freq[t]||0)+1;
  const scores = sentences.map(s=>{
    const st = tokenize(s);
    let sc=0;
    for(const t of st) sc += (freq[t] || 0);
    return {s, sc};
  });
  scores.sort((a,b)=> b.sc - a.sc);
  return scores[0].s.trim();
}

/* -------------------------
   UI: typing/streaming effect
   ------------------------- */
let typingCancelToken = { cancelled:false };

function clearTypingToken(){ typingCancelToken.cancelled = true; typingCancelToken = { cancelled:false }; }

async function streamTextToElement(text, el, speed=18){
  clearTypingToken();
  el.textContent = '';
  for(let i=0;i<text.length;i++){
    if(typingCancelToken.cancelled) return;
    el.textContent += text[i];
    // subtle HAL eye flicker on punctuation
    if(/[.,;:!?]/.test(text[i])) animateEyePulse();
    await new Promise(r=>setTimeout(r, speed));
  }
}

/* -------------------------
   HAL eye interactions
   ------------------------- */
function animateEyePulse(){
  halEye.animate([
    { transform: 'scale(1)' },
    { transform: 'scale(1.04)' },
    { transform: 'scale(1)' }
  ], { duration: 360, easing: 'ease-in-out' });
}

/* -------------------------
   TTS
   ------------------------- */
function speakText(text){
  if(!('speechSynthesis' in window)) { alert('TTS not supported in this browser'); return; }
  window.speechSynthesis.cancel();
  const utter = new SpeechSynthesisUtterance(text);
  utter.lang = 'en-US';
  utter.rate = 0.95;
  utter.pitch = 0.9;
  utter.onstart = () => halEye.classList.add('speaking');
  utter.onend = () => halEye.classList.remove('speaking');
  window.speechSynthesis.speak(utter);
}

/* -------------------------
   STT (voice input)
   ------------------------- */
let recognition = null;
if('webkitSpeechRecognition' in window || 'SpeechRecognition' in window){
  const Constructor = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new Constructor();
  recognition.lang = 'en-US';
  recognition.interimResults = false;
  recognition.onstart = ()=> micBtn.classList.add('listening');
  recognition.onend = ()=> micBtn.classList.remove('listening');
  recognition.onresult = (ev) => {
    const text = ev.results[0][0].transcript;
    queryInput.value = text;
  };
} else {
  // not supported; show fallback tooltip
  micBtn.title = 'Voice input not supported in this browser';
}

/* -------------------------
   Main ask flow
   ------------------------- */
async function askHAL(){
  const q = queryInput.value.trim();
  if(!q){ alert('Please type a question for HAL.'); return; }
  animateEyePulse();
  responseDiv.textContent = '...';
  sourcesDiv.textContent = '';
  clearTypingToken();

  const k = Math.max(1, Math.min(10, parseInt(topKInput.value || '3')));
  const retrieved = retrieve(q, k);

  // show top sources
  if(retrieved.length){
    sourcesDiv.innerHTML = `<strong>Top sources:</strong> ${[...new Set(retrieved.map(r=>r.docId))].join(', ')}`;
  } else {
    sourcesDiv.innerHTML = `<strong>Top sources:</strong> none`;
  }

  // choose generation mode
  const mode = modeSelect.value; // 'mock' or 'remote'
  if(mode === 'mock'){
    const out = mockGenerate(q, retrieved);
    await streamTextToElement(out, responseDiv, 16);
  } else {
    // remote mode: POST to /api/generate with { query, contexts }
    // There's an example below: you should implement a secure server-side endpoint that calls the language model (do NOT call external LMs from the browser)
    try{
      const payload = {
        query: q,
        contexts: retrieved.map(r=>({docId:r.docId, text:r.text})),
        topK: k
      };

      // Example: this is a placeholder endpoint. Replace with your server endpoint.
      const endpoint = '/api/generate'; // <-- implement on your server

      // If the user did not set up a remote endpoint, fallback to mock.
      if(!useRemote.checked){
        const out = mockGenerate(q, retrieved);
        await streamTextToElement(out, responseDiv, 16);
      } else {
        // perform request
        responseDiv.textContent = 'Contacting remote backend...';
        const res = await fetch(endpoint, {
          method: 'POST',
          headers: {'Content-Type':'application/json'},
          body: JSON.stringify(payload),
        });
        if(!res.ok) throw new Error('Remote backend error: ' + res.status);
        // We support two response flavors: streaming text, or {answer, sources}
        const ct = res.headers.get('content-type') || '';
        if(ct.includes('text/event-stream') || ct.includes('text/plain')) {
          // stream text
          const reader = res.body.getReader();
          const decoder = new TextDecoder();
          responseDiv.textContent = '';
          while(true){
            const {done, value} = await reader.read();
            if(done) break;
            const chunk = decoder.decode(value);
            responseDiv.textContent += chunk;
            // autopulse
            animateEyePulse();
          }
        } else {
          const json = await res.json();
          const ans = json.answer || JSON.stringify(json);
          await streamTextToElement(ans, responseDiv, 16);
          if(json.sources) sourcesDiv.innerHTML = `<strong>Sources:</strong> ${json.sources.join(', ')}`;
        }
      }
    }catch(err){
      // fallback to mock answer but show error
      console.error(err);
      const msg = `Remote request failed; falling back to local demo.\n\nError: ${err.message}`;
      await streamTextToElement(msg + '\n\n' + mockGenerate(q, retrieved), responseDiv, 14);
    }
  }
}

/* -------------------------
   Buttons / handlers
   ------------------------- */
askBtn.addEventListener('click', askHAL);
queryInput.addEventListener('keydown', (e)=>{ if(e.key === 'Enter') askHAL(); });

speakBtn.addEventListener('click', ()=>{
  const txt = responseDiv.textContent.trim();
  if(!txt) return alert('No answer to speak. Ask HAL first.');
  speakText(txt);
});

micBtn.addEventListener('click', ()=>{
  if(!recognition) { alert('Speech recognition not supported in this browser'); return; }
  try{
    recognition.start();
  }catch(e){
    console.warn('Recognition start error', e);
  }
});

/* -------------------------
   Example: helper to wire a quick demo KB for testing
   ------------------------- */
function seedDemo(){
  addDocument('HAL Manual', `
  HAL 9000 is the Heuristically Programmed ALgorithmic computer. This is a demo knowledge base. The HAL interface here is merely aesthetic and does not imply any real HAL.
  The knowledge base stores chunks of text and the frontend calculates lightweight term-frequency similarity to retrieve relevant passages.
  `);

  addDocument('Mission Logs', `
  Mission log: During the mission, the crew observed unusual telemetry. The onboard computer flagged anomalies in the thermal system and recommended re-routing power from nonessential systems.
  `);

  addDocument('2001 Analysis', `
  In the film, HAL is presented as an intelligent agent with voice interface, and considerations about reliability and ethics are central. This demo intentionally presents a calm, minimalist HAL-like interface.
  `);
}

// seed for convenience
seedDemo();
renderKb();

/* -------------------------
   FINAL: safety visual tweak - hal eye glow while speaking
   ------------------------- */
const style = document.createElement('style');
style.textContent = `
#halEye.speaking .hal-lens { box-shadow: 0 0 44px rgba(255,60,60,0.4), inset 0 12px 60px rgba(255,80,80,0.12); transform: scale(1.05); }
`;
document.head.appendChild(style);

/* -------------------------
   Expose a tiny debug function to window for quick testing in console
   ------------------------- */
window.__HAL_DEBUG = { docs, chunks, retrieve };
