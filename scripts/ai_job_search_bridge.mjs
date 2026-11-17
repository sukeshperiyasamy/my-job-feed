// Node 24 runs the borrowed dependency-free TypeScript without installing Bun.
import { registerHooks } from 'node:module';
import { fileURLToPath } from 'node:url';
import { existsSync } from 'node:fs';
const base=new URL('../integrations/ai-job-search/freehire/',import.meta.url);
registerHooks({resolve(specifier,context,nextResolve){
  if(context.parentURL?.startsWith(base.href)&&specifier.endsWith('.js')){
    const target=new URL(specifier.slice(0,-3)+'.ts',context.parentURL);
    if(target.href.startsWith(base.href)&&existsSync(fileURLToPath(target)))return nextResolve(target.href,context);
  }
  return nextResolve(specifier,context);
}});
process.env.FREEHIRE_API_URL='https://freehire.me';
// Fixed destination, no profile/cookies and no cross-host redirects.
const originalFetch=globalThis.fetch;
globalThis.fetch=(url,options={})=>{
  const target=new URL(url);
  if(target.origin!=='https://freehire.me'||!target.pathname.startsWith('/api/v1/'))throw Error('Unsupported API destination');
  return originalFetch(url,{...options,redirect:'error'});
};
let input='';for await(const chunk of process.stdin){input+=chunk;if(input.length>10000)throw Error('Input too large');}
try{
  const body=JSON.parse(input);
  if(body.operation==='health'){
    await import(new URL('commands/search.ts',base));
    process.stdout.write(JSON.stringify({ready:true,node:process.version,source:'freehire'}));
  }else if(body.operation==='search'){
    if(typeof body.query!=='string'||body.query.length>180)throw Error('Invalid query');
    const {runSearch}=await import(new URL('commands/search.ts',base));
    process.exitCode=await runSearch({query:body.query,jobage:Math.min(90,Math.max(1,body.days||30)),page:1,limit:Math.min(50,Math.max(1,body.limit||25)),format:'json',descriptionFormat:'text',includeDescription:true,regions:body.remote?['global']:[],countries:body.remote?[]:['IN'],cities:[],seniority:[],category:[],skills:[],facets:{},...(body.remote?{workMode:'remote'}:{})});
  }else throw Error('Unsupported operation');
}catch(e){process.stderr.write(JSON.stringify({error:e.message}));process.exitCode=1;}
