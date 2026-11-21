import React,{useEffect,useRef,useState} from 'react';
import {loadFloorPlan} from './floorPlanClient.js';

/** Read-only diagnostic: never substitutes fetched data for demo seating until Python RBAC is verified. */
export default function PythonFloorPlanPreview(){
  const [state,setState]=useState({status:'idle',data:null,message:''});
  const pending=useRef(null);
  useEffect(()=>()=>pending.current?.abort(),[]);
  async function refresh(){
    pending.current?.abort();
    const controller=new AbortController();
    pending.current=controller;
    setState({status:'loading',data:null,message:''});
    try{
      const data=await loadFloorPlan({signal:controller.signal});
      if(!controller.signal.aborted)setState({status:'ready',data,message:''});
    }catch(error){
      if(!controller.signal.aborted)setState({status:'error',data:null,message:error?.code==='AUTH'?'Authentication or venue authorization required.':'Python floor-plan API unavailable or returned invalid data.'});
    }finally{
      if(pending.current===controller)pending.current=null;
    }
  }
  const {status,data,message}=state;
  return <section className="panel" aria-label="Python floor-plan connectivity" data-testid="python-floor-preview">
    <h3>Python floor-plan read · integration preview</h3>
    <p className="muted">Optional read-only connectivity check. The editable floor plan and seating above remain synthetic demo state. No backend changes are sent.</p>
    <button type="button" onClick={refresh} disabled={status==='loading'}>{status==='loading'?'Checking Python API…':'Check authenticated Python floor plan'}</button>
    {status==='loading'&&<p role="status">Loading authenticated floor-plan data…</p>}
    {status==='error'&&<p role="alert">{message}</p>}
    {status==='ready'&&<div role="status"><p>Authenticated response · revision {data.revision} · {data.tables.length} physical tables · {Object.keys(data.positions).length} placements</p>
      {data.tables.length===0?<p>No physical tables are configured for this venue.</p>:<ul>{data.tables.map(t=><li key={t.id}>{t.id}: {t.guests} of {t.seats} seats · {Object.hasOwn(data.positions,t.id)?'placed':'unplaced'}</li>)}</ul>}
    </div>}
  </section>;
}
