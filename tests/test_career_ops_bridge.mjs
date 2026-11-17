import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {collect,resolveSource,verify} from '../scripts/career_ops_bridge.mjs';
const config=JSON.parse(readFileSync(new URL('../config/career-ops.json',import.meta.url),'utf8'));
for(const source of config.sources)await resolveSource(source);
await assert.rejects(resolveSource({provider:'local-parser',url:'https://example.com'}),/Unsupported/);
await assert.rejects(resolveSource({provider:'lever',url:'https://example.com'}),/not a supported/);
await assert.rejects(resolveSource({provider:'lever',url:'https://user:secret@jobs.lever.co/example'}),/without credentials/);
const gh=await collect({name:'Fixture',provider:'greenhouse',url:'https://job-boards.greenhouse.io/fixture'},{fetchJson:async()=>({jobs:[{id:12,title:'Junior Firmware Engineer',absolute_url:'https://job-boards.greenhouse.io/fixture/jobs/12',location:{name:'Bengaluru'},content:'<p>0-2 years experience with ESP32</p>'}]})});
assert.equal(gh.jobs[0].listingIdentity.posting_id,'12');assert.match(gh.jobs[0].description,/ESP32/);
const lever=await collect({name:'Fixture',provider:'lever',url:'https://jobs.lever.co/fixture'},{fetchJson:async()=>[{id:'abc',text:'Junior Python Developer',hostedUrl:'https://jobs.lever.co/fixture/abc',categories:{location:'Chennai'},descriptionPlain:'Python and SQL',workplaceType:'onsite'}]});
assert.equal(lever.jobs[0].location,'Chennai');assert.match(lever.jobs[0].description,/Python/);
const ashby=await collect({name:'Fixture',provider:'ashby',url:'https://jobs.ashbyhq.com/fixture'},{fetchJson:async()=>({jobs:[{id:'abc',title:'Junior Engineer',jobUrl:'https://jobs.ashbyhq.com/fixture/abc',location:'India',descriptionPlain:'Software testing'}]})});
assert.equal(ashby.jobs.length,1);
const originalFetch=globalThis.fetch;
try{
 globalThis.fetch=async()=>new Response('{}',{status:404});
 assert.equal((await verify('https://job-boards.greenhouse.io/fixture/jobs/12',false)).result,'expired');
 globalThis.fetch=async()=>new Response('{}',{status:429});
 assert.equal((await verify('https://job-boards.greenhouse.io/fixture/jobs/12',false)).result,'uncertain');
 assert.equal((await verify('https://example.com/job/1',false)).result,'uncertain');
 await assert.rejects(verify('http://127.0.0.1:8000',true),/private|denied/i);
}finally{globalThis.fetch=originalFetch}
console.log('Career Ops adapter: source validation, three actual provider parsers, expiry/uncertainty and private-network guards passed.');
