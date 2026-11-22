import React,{useEffect,useRef,useState} from 'react';
import {loadMenu} from './menuClient.js';
import {filterMenu} from './menuViewModel.js';
import {catalogCartLines,changeCatalogQuantity} from './catalogCart.js';

const eur=cents=>new Intl.NumberFormat('en-BE',{style:'currency',currency:'EUR'}).format(cents/100);

/** Local, non-checkout cart backed exclusively by authenticated venue menu records. */
export default function CatalogPos(){
  const [state,setState]=useState({status:'loading',items:[],error:''});
  const [query,setQuery]=useState('');
  const searchRef=useRef(null);
  const [kind,setKind]=useState('all');
  const [availableOnly,setAvailableOnly]=useState(false);
  const [quantities,setQuantities]=useState({});
  const [notice,setNotice]=useState('');
  const [retry,setRetry]=useState(0);
  useEffect(()=>{
    const controller=new AbortController();
    setState({status:'loading',items:[],error:''});
    setQuantities({});
    loadMenu({signal:controller.signal}).then(items=>{
      if(!controller.signal.aborted){
        setState({status:'ready',items,error:''});
        if(retry>0)setNotice('Catalog refreshed. The previous local draft was cleared.');
      }
    }).catch(error=>{
      if(!controller.signal.aborted)setState({status:'error',items:[],error:error?.code==='AUTH'?'Sign in with menu access to view this catalog.':'Authenticated menu unavailable. No demo items substituted.'});
    });
    return ()=>controller.abort();
  },[retry]);
  const items=state.status==='ready'?state.items:[];
  const shown=filterMenu(items,query,kind,availableOnly);
  let projection;
  let draftInvalid=false;
  try{projection=catalogCartLines(items,quantities);}
  catch{draftInvalid=true;projection={lines:[],totalCents:0};}
  function adjust(id,delta){
    try{const next=changeCatalogQuantity(items,quantities,id,delta);setQuantities(next);setNotice('');}
    catch{setNotice('Item unavailable or cart quantity limit reached. Refresh the catalog.');}
  }
  return <section className="panel" aria-label="Authenticated catalog POS">
    <h2>Live catalog · Order draft</h2>
    <p className="muted">Venue-scoped Python catalog. Draft only: no kitchen submission, checkout or payment. Prices must be recalculated by the server before any future order is accepted.</p>
    {state.status==='loading'&&<p role="status">Loading authenticated menu…</p>}
    {state.status==='error'&&<><p role="alert">{state.error}</p><button type="button" onClick={()=>setRetry(n=>n+1)}>Retry catalog</button></>}
    {state.status==='ready'&&<>
      <div className="filters" role="search" aria-label="Filter authenticated venue catalog">
        <input ref={searchRef} type="search" aria-label="Search live POS catalog" aria-controls="catalog-pos-results" value={query} onChange={e=>setQuery(e.target.value)} onKeyDown={e=>{if(e.key==='Escape'&&query){e.preventDefault();setQuery('');}}} aria-keyshortcuts="Escape" placeholder="Search food and drinks"/>
        {query.length>0&&<button type="button" onClick={()=>{setQuery('');searchRef.current?.focus();}} aria-label="Clear live catalog search">Clear search</button>}
        <select aria-label="Live POS product type" value={kind} onChange={e=>setKind(e.target.value)}><option value="all">All</option><option value="food">Food</option><option value="drink">Drinks</option></select>
        <label><input type="checkbox" checked={availableOnly} onChange={e=>setAvailableOnly(e.target.checked)}/> Available only</label>
        <button type="button" onClick={()=>setRetry(n=>n+1)}>Refresh catalog</button>
      </div>
      <p role="status" className="muted">{shown.length} of {items.length} venue products shown</p>
      <div className="columns"><div id="catalog-pos-results" className="dishes">
        {shown.map(item=><article className="dish" key={item.id}><div><small>{item.kind==='food'?'Food':'Drink'} · {item.available?'Available':'Unavailable'}</small><h3>{item.name}</h3>{item.description&&<p>{item.description}</p>}<div className="dish-foot"><b>{eur(item.priceCents)}</b><button type="button" disabled={!item.available} onClick={()=>adjust(item.id,1)} aria-label={'Add '+item.name+' to catalog draft'}>+ Add</button></div></div></article>)}
        {shown.length===0&&(items.length===0?<p role="status">No products configured for this venue.</p>:<div><p role="status">No matching venue products. Clear the filters to show all products.</p><button type="button" onClick={()=>{setQuery('');setKind('all');setAvailableOnly(false);searchRef.current?.focus();}}>Clear catalog filters</button></div>)}
      </div><aside className="panel"><h3>Catalog draft</h3>
        {draftInvalid&&<p role="alert">This draft no longer matches the authenticated catalog. Clear it or refresh the catalog before selecting products.</p>}
        {projection.lines.length===0&&<p className="muted">No catalog items selected.</p>}
        {projection.lines.map(line=><div className="cart-row" key={line.id}><span>{line.name} · {eur(line.lineCents)}</span><button type="button" aria-label={'Remove one '+line.name+' from catalog draft; '+line.quantity+' currently selected'} onClick={()=>adjust(line.id,-1)}>−</button><b aria-label={line.quantity+' '+line.name+' in catalog draft'}>{line.quantity}</b><button type="button" aria-label={'Add one '+line.name+' to catalog draft; '+line.quantity+' currently selected'} onClick={()=>adjust(line.id,1)}>+</button></div>)}
        <p className="sr-only" role="status" aria-live="polite">{projection.lines.reduce((count,line)=>count+line.quantity,0)} items in catalog draft; total {eur(projection.totalCents)}. No order has been submitted.</p>
        <div className="total"><span>Draft total</span><b>{eur(projection.totalCents)}</b></div>
        <button type="button" disabled={!draftInvalid&&projection.lines.length===0} onClick={()=>{setQuantities({});setNotice('Draft cleared.');}}>Clear draft</button>
        {notice&&<p role="status">{notice}</p>}
        <p className="muted">Not an order or receipt. This draft is lost on refresh; no payment is processed.</p>
      </aside></div>
    </>}
  </section>;
}
