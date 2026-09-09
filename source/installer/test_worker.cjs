'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {createHash, webcrypto} = require('node:crypto');
const app = require('./app.js');
const hash = b => createHash('sha256').update(b).digest('hex');
const array = b => Uint8Array.from(b).buffer;
const original = Buffer.from(Array.from({length:8192}, (_,i)=>i%251));
const targetBytes = Buffer.concat([original.subarray(0,2500),Buffer.from('new synthetic game'.repeat(180))]);
function release() {
  return {schema:1,version:'1.04',target:{id:'en-plus',language:'US',camera:'New Angle',sha256:hash(targetBytes),bytes:targetBytes.length,output_name:'Sacred Gold Plus - New Angle - US.nds'},sources:Array.from({length:4},(_,i)=>({id:['clean-us','plus-1.01','plus-1.02','plus-1.03'][i],label:'Source '+i,sha256:hash(i?Buffer.concat([original,Buffer.from([i])]):original),bytes:original.length+(i?1:0),patch:{sha256:'a'.repeat(64),bytes:6,data:'1sPEAAAA'}}))};
}
function file(b) { return {size:b.length,arrayBuffer:async()=>array(b)}; }
test('unknown size is refused before reading any bytes',async()=>{
  let reads=0;
  await assert.rejects(app.classifyFile({size:1,arrayBuffer:async()=>{reads++;return array([1]);}},release()),/UNKNOWN_SIZE/);
  assert.equal(reads,0);
});
test('known size but unknown whole-file hash is refused',async()=>{
  await assert.rejects(app.classifyFile(file(Buffer.alloc(original.length)),release()),/UNKNOWN_INPUT/);
});
test('exact known source selected and original bytes kept',async()=>{
  const r=await app.classifyFile(file(original),release());
  assert.equal(r.kind,'source'); assert.equal(r.source.id,'clean-us');
  assert.deepEqual(Buffer.from(r.buffer),original);
});
test('already target is a no-op without an output buffer',async()=>{
  const r=await app.classifyFile(file(targetBytes),release());
  assert.equal(r.kind,'current');assert.equal(r.buffer,undefined);
});
test('ambiguous source manifest is refused',async()=>{
  const r=release();r.sources[1]=structuredClone(r.sources[0]);
  await assert.rejects(app.classifyFile(file(original),r),/MANIFEST/);
});
// Generated with xdelta3 3.1.0: -e -A -S none -D -s source target patch.
// Both source and target are the synthetic byte arrays above; no game data.
const patchBytes=Buffer.from('1sPEAAAFk0QAJqxsABIIAqeFq9NuZXcgc3ludGhldGljIGdhbWUTk0QBEiOZFgAS','base64');
async function worker(job) {
  const messages=[];
  const self={postMessage:m=>messages.push(m)};
  const context=vm.createContext({self,crypto:webcrypto,atob,ArrayBuffer,Uint8Array,DataView,TextEncoder,console});
  const vendors=['HashCalculator.js','BinFile.js','RomPatcher.format.vcdiff.js'];
  const code=vendors.map(n=>fs.readFileSync(path.join(__dirname,'vendor',n),'utf8')).join('\n')+'\n'+fs.readFileSync(path.join(__dirname,'worker.js'),'utf8');
  vm.runInContext(code,context);
  await self.onmessage({data:job});
  return messages;
}
function job() {
  const r=release();
  r.sources[0].patch={sha256:hash(patchBytes),bytes:patchBytes.length,data:patchBytes.toString('base64')};
  return {input:array(original),source:r.sources[0],target:r.target};
}
test('real xdelta decoded by exact browser vendor bytes',async()=>{
  const j=job(),before=Buffer.from(j.input).toString('hex');
  const messages=await worker(j),result=messages.at(-1);
  assert.equal(result.type,'ready');assert.deepEqual(Buffer.from(result.buffer),targetBytes);
  assert.equal(Buffer.from(j.input).toString('hex'),before);
});
for(const field of ['input','patchHash','patchSize','outputHash','outputSize']) {
  test('worker refuses '+field+' mismatch without downloadable result',async()=>{
    const j=job();
    if(field==='input')new Uint8Array(j.input)[0]^=1;
    if(field==='patchHash')j.source.patch.sha256='0'.repeat(64);
    if(field==='patchSize')j.source.patch.bytes++;
    if(field==='outputHash')j.target.sha256='0'.repeat(64);
    if(field==='outputSize')j.target.bytes++;
    const messages=await worker(j);
    assert.equal(messages.at(-1).type,'error');assert.equal(messages.some(m=>m.type==='ready'),false);
    assert.equal(messages.at(-1).code,field==='input'?'INPUT':field.startsWith('patch')?'PATCH':'OUTPUT');
  });
}
test('invalid VCDIFF header is refused without a result',async()=>{
  const j=job(),bad=Buffer.from('invalid delta');
  j.source.patch={sha256:hash(bad),bytes:bad.length,data:bad.toString('base64')};
  const messages=await worker(j);
  assert.equal(messages.at(-1).type,'error');assert.equal(messages.some(m=>m.type==='ready'),false);
});

test('all four source identities are selected by hash, not label',async()=>{
  const r=release();
  for(let i=0;i<4;i++) {
    const input=i?Buffer.concat([original,Buffer.from([i])]):original;
    r.sources[i].label='Identical misleading label';
    const result=await app.classifyFile(file(input),r);
    assert.equal(result.source.id,['clean-us','plus-1.01','plus-1.02','plus-1.03'][i]);
  }
});
test('missing native crypto refuses before reading supported file',async()=>{
  const descriptor=Object.getOwnPropertyDescriptor(globalThis,'crypto');
  let reads=0;
  try {
    Object.defineProperty(globalThis,'crypto',{value:undefined,configurable:true});
    await assert.rejects(app.classifyFile({size:original.length,arrayBuffer:async()=>{reads++;return array(original);}},release()),/CRYPTO/);
    assert.equal(reads,0);
  } finally {
    if(descriptor)Object.defineProperty(globalThis,'crypto',descriptor);else delete globalThis.crypto;
  }
});
test('pinned vendor files match independent recorded fingerprints',()=>{
  const manifest=JSON.parse(fs.readFileSync(path.join(__dirname,'vendor-manifest.json'),'utf8'));
  for(const row of manifest.files) {
    const b=fs.readFileSync(path.join(__dirname,row.path));
    assert.equal(hash(b),row.sha256);assert.equal(b.length,row.bytes);
  }
});


// A small DOM/Worker boundary exercises the actual mounted app and its async
// event handlers. No browser, game-sized input or decoder allocation required.
function mountedApp(read = async()=>array(original)) {
  const elements={},events={},workers=[],revoked=[];
  function element() {
    return {disabled:false,hidden:true,textContent:'',files:[],handlers:{},
      setAttribute(k,v){this[k]=v;},removeAttribute(k){delete this[k];},
      addEventListener(k,fn){this.handlers[k]=fn;},focus(){}};
  }
  for(const id of ['game-file','install','status','download','progress','installer','release-data','worker-source'])elements[id]=element();
  elements['release-data'].textContent=JSON.stringify(release());
  elements['worker-source'].textContent=JSON.stringify('/* synthetic worker boundary */');
  const selected={size:original.length,arrayBuffer:read};
  elements['game-file'].files=[selected];
  class MockWorker {
    constructor(){this.terminated=false;workers.push(this);}
    postMessage(job){this.job=job;}
    terminate(){this.terminated=true;}
  }
  class MockFile {}
  MockFile.prototype.arrayBuffer=()=>{};
  let nextURL=0;
  const context=vm.createContext({document:{documentElement:{lang:'en'},querySelectorAll:()=>[],getElementById:id=>elements[id]},
    crypto:webcrypto,Worker:MockWorker,File:MockFile,Blob,ArrayBuffer,Uint8Array,
    URL:{createObjectURL:()=>`blob:fixture-${++nextURL}`,revokeObjectURL:url=>revoked.push(url)},
    addEventListener:(type,listener)=>{events[type]=listener;}});
  vm.runInContext(fs.readFileSync(path.join(__dirname,'app.js'),'utf8'),context);
  elements['game-file'].handlers.change();
  return {elements,workers,selected,revoked,
    click:()=>elements.install.handlers.click(),
    leave:()=>events.pagehide({persisted:true}),
    restore:()=>{if(events.pageshow)events.pageshow({persisted:true});}};
}

test('pagehide while worker runs restores usable controls on pageshow',async()=>{
  const ui=mountedApp();await ui.click();
  assert.equal(ui.workers.length,1);
  assert.equal(ui.elements.install.disabled,true);
  ui.leave();ui.restore();
  assert.equal(ui.workers[0].terminated,true);
  assert.equal(ui.elements['game-file'].disabled,false);
  assert.equal(ui.elements.install.disabled,false);
  assert.equal(ui.elements.progress.hidden,true);
  assert.equal(ui.elements.installer['aria-busy'],'false');
  assert.match(ui.elements.status.textContent,/interrupted|cancelled/i);
  await ui.click();assert.equal(ui.workers.length,2);
});

test('classification finishing after pagehide cannot start an old worker',async()=>{
  let resolve;
  const ui=mountedApp(()=>new Promise(r=>{resolve=r;}));
  const oldClick=ui.click();
  ui.leave();ui.restore();
  resolve(array(original));await oldClick;
  assert.equal(ui.workers.length,0);
  assert.equal(ui.elements.install.disabled,false);
  assert.equal(ui.elements.progress.hidden,true);
});

test('late classification failure cannot cancel a newer operation',async()=>{
  let reject;
  const ui=mountedApp(()=>new Promise((_,r)=>{reject=r;}));
  const oldClick=ui.click();ui.leave();ui.restore();
  ui.selected.arrayBuffer=async()=>array(original);
  await ui.click();
  assert.equal(ui.workers.length,1);
  const active=ui.workers[0];
  const message=ui.elements.status.textContent;
  reject(new Error('READ'));await oldClick;
  assert.equal(active.terminated,false);
  assert.equal(ui.elements.install.disabled,true);
  assert.equal(ui.elements.status.textContent,message);
});

test('old worker progress, result and errors cannot replace a newer operation',async()=>{
  const ui=mountedApp();await ui.click();
  const old=ui.workers[0],oldMessage=old.onmessage,oldError=old.onerror;
  ui.leave();ui.restore();await ui.click();
  assert.equal(ui.workers.length,2);
  const current=ui.workers[1],message=ui.elements.status.textContent;
  for(const data of [{type:'progress',stage:'decoding'},
      {type:'ready',buffer:array(targetBytes)},{type:'error',code:'OUTPUT'}])oldMessage({data});
  oldError({preventDefault(){}});
  assert.equal(current.terminated,false);
  assert.equal(ui.elements.status.textContent,message);
  assert.equal(ui.elements.download.hidden,true);
  assert.equal(ui.elements.install.disabled,true);
  current.onmessage({data:{type:'ready',buffer:array(targetBytes)}});
  assert.equal(ui.elements.download.hidden,false);
  assert.equal(ui.elements.download.download,'Sacred Gold Plus - New Angle - US.nds');
});

test('pagehide revokes completed download and pageshow does not claim it is ready',async()=>{
  const ui=mountedApp();await ui.click();
  ui.workers[0].onmessage({data:{type:'ready',buffer:array(targetBytes)}});
  const url=ui.elements.download.href;
  assert.equal(ui.elements.download.hidden,false);
  ui.leave();ui.restore();
  assert.equal(ui.elements.download.hidden,true);
  assert.equal(ui.revoked.includes(url),true);
  assert.equal(ui.elements.install.disabled,false);
  assert.doesNotMatch(ui.elements.status.textContent,/Verified\. Download/);
});
