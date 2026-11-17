// Thin read-only adapter. Never run Career Ops' application, tracker or AI CLIs.
import { readFileSync,existsSync } from 'node:fs';
import { pathToFileURL,fileURLToPath } from 'node:url';
import path from 'node:path';
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const REPO=path.join(ROOT,'apps','career-ops');
export const PROVIDERS=['greenhouse','lever','ashby','smartrecruiters','recruitee','himalayas','remotive','weworkremotely'];
const moduleAt=relative=>import(pathToFileURL(path.join(REPO,relative)).href);
export async function resolveSource(source){
 if(!PROVIDERS.includes(source.provider))throw Error('Unsupported provider.');
 const url=new URL(source.url);
 if(url.protocol!=='https:'||url.username||url.password)throw Error('Use an HTTPS public career board without credentials.');
 const provider=(await moduleAt('providers/'+source.provider+'.mjs')).default;
 const entry={name:String(source.name||'Employer'),provider:source.provider,careers_url:source.url,max_pages:2,fetchDetails:true,detail_limit:8};
 const feedHost={himalayas:'himalayas.app',remotive:'remotive.com',weworkremotely:'weworkremotely.com'}[source.provider];
 if(feedHost&&url.hostname!==feedHost)throw Error('Use the official source hostname.');
 if(!feedHost&&!provider.detect?.(entry))throw Error('The URL is not a supported board for this provider.');
 return {provider,entry};
}
export async function collect(source,injectedContext){
 const {provider,entry}=await resolveSource(source);
 const http=await moduleAt('providers/_http.mjs');let requests=0;
 const wrap=fn=>async(url,opts={})=>{if(++requests>12)throw Error('Per-source request budget reached.');return fn(url,{...opts,timeoutMs:Math.min(opts.timeoutMs||15000,20000),maxBytes:Math.min(opts.maxBytes||8*1024*1024,8*1024*1024)})};
 const ctx=injectedContext||{transport:'http',fetchJson:wrap(http.fetchJson),fetchText:wrap(http.fetchText),fetchResponse:wrap(http.fetchResponse),maxPages:2};
 const jobs=await provider.fetch(entry,ctx);
 if(!Array.isArray(jobs))throw Error('Provider did not return a job list.');
 const {boardTruncation}=await moduleAt('lib/board-truncation.mjs');
 return {jobs:jobs.slice(0,400).map(j=>({...j,description:String(j.description||'').slice(0,24000)})),fetched:jobs.length,
  partial:jobs.length>400||!!boardTruncation(jobs)||requests>=12||(['himalayas','smartrecruiters'].includes(source.provider)&&requests>=2),
  note:'Bounded to two pages, twelve requests and 400 returned listings per source; this is not an exhaustive board crawl.'};
}
export async function verify(url,browserFallback=false){
 const parsed=new URL(url);if(!['https:','http:'].includes(parsed.protocol)||parsed.username||parsed.password)throw Error('Invalid posting URL.');
 const api=await moduleAt('liveness-api.mjs');let verdict=await api.checkLivenessViaApi(url);
 if(verdict)return {...verdict,method:'api'};
 if(!browserFallback)return {result:'uncertain',code:'no_api_verdict',reason:'No decisive supported API result. Review the original posting.',method:'api'};
 const browserHelpers=await moduleAt('liveness-browser.mjs');
 const security=await browserHelpers.validateUrlSecurity(url);
 if(security) return {result:'uncertain',code:'unsafe_url',reason:'Posting URL failed public-network validation.',method:'browser'};
 const {robotsAllows}=await moduleAt('robots-check.mjs');
 const robots=await robotsAllows(url);
 if(!robots.allowed)return {result:'uncertain',code:robots.code,reason:robots.reason,method:'browser'};
 const {chromium}=await moduleAt('node_modules/playwright/index.mjs');
 const executablePath=['C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe','C:/Program Files/Google/Chrome/Application/chrome.exe'].find(existsSync);
 const browser=await chromium.launch({headless:true,...(executablePath?{executablePath}: {})});
 try{
  const page=await browserHelpers.newLivenessPage(browser);
  const result=await browserHelpers.checkUrlLiveness(page,url,{timeoutRetry:false});
  // No headed retry, login, CAPTCHA solving, clicks or submission.
  return {...result,method:'anonymous browser'};
 }finally{await browser.close()}
}
async function main(){
 const input=await new Promise((resolve,reject)=>{let data='';process.stdin.setEncoding('utf8');process.stdin.on('data',chunk=>{data+=chunk;if(data.length>64000)reject(Error('Input too large'))});process.stdin.on('end',()=>{try{resolve(JSON.parse(data))}catch(e){reject(e)}})});
 let result;
 if(input.operation==='health'){
  for(const id of PROVIDERS)await moduleAt('providers/'+id+'.mjs');await moduleAt('liveness-api.mjs');
  const pkg=JSON.parse(readFileSync(path.join(REPO,'package.json'),'utf8'));
  result={ready:true,version:pkg.version,node:process.version,providers:PROVIDERS};
 }else if(input.operation==='inspect'){await resolveSource(input.source);result={supported:true}}
 else if(input.operation==='collect')result=await collect(input.source);
 else if(input.operation==='verify')result=await verify(input.url,!!input.browser_fallback);
 else throw Error('Unsupported operation.');
 process.stdout.write(JSON.stringify(result));
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 console.log=(...args)=>console.error(...args);
 main().catch(e=>{process.stdout.write(JSON.stringify({error:e.message}));process.exitCode=1});
}
