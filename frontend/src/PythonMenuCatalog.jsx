import React,{useEffect,useRef,useState} from 'react';
import {loadMenu} from './menuClient.js';
import {filterMenu,sortMenu} from './menuViewModel.js';
const eur=cents=>new Intl.NumberFormat('en-BE',{style:'currency',currency:'EUR'}).format(cents/100);
/** Authenticated read-only menu: never substitutes hardcoded demo dishes on failure. */
export default function PythonMenuCatalog(){
 const [state,setState]=useState({status:'loading',items:[],error:''});
 const [query,setQuery]=useState('');
 const searchRef=useRef(null);
 const [kind,setKind]=useState('all');
 const [availableOnly,setAvailableOnly]=useState(false);
 const [sortOrder,setSortOrder]=useState('default');
 const [retry,setRetry]=useState(0);
 useEffect(()=>{
   const controller=new AbortController();
   setState({status:'loading',items:[],error:''});
   loadMenu({signal:controller.signal}).then(items=>{
     if(!controller.signal.aborted)setState({status:'ready',items,error:''});
   }).catch(error=>{
     if(!controller.signal.aborted)setState({status:'error',items:[],error:error?.code==='AUTH'?'Sign in with menu access to view this catalog.':'Menu catalog unavailable. Check the local authenticated Python service.'});
   });
   return ()=>controller.abort();
 },[retry]);
 const shown=state.status==='ready'?sortMenu(filterMenu(state.items,query,kind,availableOnly),sortOrder):[];
 return <section className="panel" aria-label="Python food and drink catalog">
  <h2>Food &amp; Drink · Python catalog</h2>
  <p className="muted">Authenticated read-only catalog. Any entries shown are from the Python API; the separate demo POS is not connected to this catalog.</p>
  {state.status==='loading'&&<p role="status">Loading food and drinks…</p>}
  {state.status==='error'&&<><p role="alert">{state.error}</p><button type="button" onClick={()=>setRetry(n=>n+1)}>Retry menu load</button></>}
  {state.status==='ready'&&<>
   <div className="filters">
    <input ref={searchRef} type="search" aria-label="Search catalog" aria-controls="python-menu-results" aria-keyshortcuts="Escape" placeholder="Search food and drinks" value={query} onChange={e=>setQuery(e.target.value)} onKeyDown={e=>{if(e.key==='Escape'&&query){e.preventDefault();setQuery('');}}}/>
    {query.length>0&&<button type="button" onClick={()=>{setQuery('');searchRef.current?.focus();}} aria-label="Clear catalog search">Clear search</button>}
    <select aria-label="Catalog type" value={kind} onChange={e=>setKind(e.target.value)}><option value="all">All</option><option value="food">Food</option><option value="drink">Drinks</option></select>
    <label><input type="checkbox" checked={availableOnly} onChange={e=>setAvailableOnly(e.target.checked)}/> Available only</label>
    <select aria-label="Sort catalog" value={sortOrder} onChange={e=>setSortOrder(e.target.value)}><option value="default">API order</option><option value="name">Name A–Z</option><option value="price-low">Price: low to high</option><option value="price-high">Price: high to low</option></select>
   </div>
   {(query.trim()!==''||kind!=='all'||availableOnly||sortOrder!=='default')&&<button type="button" onClick={()=>{setQuery('');setKind('all');setAvailableOnly(false);setSortOrder('default');searchRef.current?.focus();}} aria-label="Reset catalog filters">Reset filters</button>}
   <p id="python-menu-result-count" role="status" aria-live="polite" aria-atomic="true" className="muted">{shown.length} of {state.items.length} catalog items shown</p>
   <div id="python-menu-results" className={shown.length===0?'':'dishes'} role="region" aria-label="Catalog results" aria-describedby="python-menu-result-count">
    {shown.length===0?<p>{state.items.length===0?'No menu items configured for this venue.':'No matching food or drinks.'}</p>:
     shown.map(item=><article className="dish" key={item.id}><div><small>{item.kind==='food'?'Food':'Drink'} · {item.available?'Available':'Unavailable'}</small><h3>{item.name}</h3>{item.description&&<p>{item.description}</p>}<b>{eur(item.priceCents)}</b></div></article>)}
   </div>
  </>}
 </section>;
}
