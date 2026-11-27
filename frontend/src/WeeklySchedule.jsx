import React,{useState} from 'react';
import {DEMO_WEEK,shiftWeek,weekDays,demoRoster,weekForDate} from './demoRoster.js';
import './weeklySchedule.css';
import {rosterShiftKey,rosterShiftDescription} from './rosterShiftDetails.js';
import {createDemoShiftDraft,replaceDemoShiftDraft} from './rosterDraft.js';

export default function WeeklySchedule(){
  const [week,setWeek] = useState(DEMO_WEEK);
  const [selectedDate,setSelectedDate] = useState(DEMO_WEEK);
  const [view,setView] = useState('grid');
  const [expandedShift,setExpandedShift] = useState(null);
  const [drafts,setDrafts] = useState([]);
  const [draftOpen,setDraftOpen] = useState(false);
  const [editingDraftId,setEditingDraftId] = useState(null);
  const [copyDraft,setCopyDraft] = useState(null);
  const editingDraft=drafts.find(d=>d.id===editingDraftId)||null;
  const formDraft=editingDraft||copyDraft;
  const [draftError,setDraftError] = useState('');
  const todayParts = Object.fromEntries(new Intl.DateTimeFormat('en-GB',{timeZone:'Europe/Brussels',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date()).filter(p=>p.type!=='literal').map(p=>[p.type,p.value]));
  const today = `${todayParts.year}-${todayParts.month}-${todayParts.day}`;
  function chooseDate(value){if(!/^\d{4}-\d{2}-\d{2}$/.test(value))return;setSelectedDate(value);setWeek(weekForDate(value));setExpandedShift(null);}
  const days = weekDays(week);
  const roster = demoRoster(week);
  return <section className="roster-panel" aria-labelledby="roster-title">
    <div className="roster-heading">
      <div><h2 id="roster-title">Weekly Schedule</h2><p>Fictional roster · Europe/Brussels · planned shifts only</p></div>
      <button type="button" className="roster-action" aria-expanded={draftOpen} aria-controls="roster-draft-form" onClick={()=>{setDraftOpen(open=>!open);setEditingDraftId(null);setCopyDraft(null);setDraftError("");}}>+ Create Demo Draft</button>
    </div>
    {draftOpen&&<form id="roster-draft-form" className="roster-draft-form" onSubmit={event=>{event.preventDefault();const fields=new FormData(event.currentTarget);try{const input=Object.fromEntries(fields);if(editingDraft){setDrafts(old=>replaceDemoShiftDraft(old,editingDraft.id,input,demoRoster(DEMO_WEEK)));setEditingDraftId(null);setCopyDraft(null);setDraftOpen(false);}else{const draft=createDemoShiftDraft(input,demoRoster(DEMO_WEEK),drafts);setDrafts(old=>[...old,draft]);setCopyDraft(null);event.currentTarget.reset();}setDraftError('');}catch(error){setDraftError(error.message);}}}>
      <h3>{editingDraft?'Edit fictional shift draft':copyDraft?'Duplicate fictional shift draft':'New fictional shift draft'}</h3><p>Local preview only — not published or saved to a server.</p>
      <label>Employee<select key={formDraft?.id||"new-person"} name="personId" required defaultValue={formDraft?.personId||""}><option value="" disabled>Select fictional employee</option>{(demoRoster(DEMO_WEEK)||[]).map(person=><option value={person.id} key={person.id}>{person.name} · {person.role}</option>)}</select></label>
      <label>Date<input key={formDraft?.id||"new-date"} name="date" type="date" required defaultValue={formDraft?.date||selectedDate}/></label>
      <label>Start<input key={formDraft?.id||"new-start"} name="start" type="time" required defaultValue={formDraft?.start||"09:00"}/></label>
      <label>End<input key={formDraft?.id||"new-end"} name="end" type="time" required defaultValue={formDraft?.end||"17:00"}/></label>
      <button type="submit">{editingDraft?"Save demo changes":copyDraft?"Add duplicated demo draft":"Add demo draft"}</button>{(editingDraft||copyDraft)&&<button type="button" onClick={()=>{setEditingDraftId(null);setCopyDraft(null);setDraftOpen(false);setDraftError("");}}>Cancel</button>}
      {draftError&&<p role="alert">{draftError}</p>}
    </form>}
    {drafts.length>0&&<section className="roster-drafts" aria-label="Unsaved fictional shift drafts"><h3>Unsaved demo drafts ({drafts.length})</h3><ul>{drafts.map(draft=><li key={draft.id}>{draft.personName} · {draft.date} · {draft.start}–{draft.end}{draft.overnight?' (+1 day)':''} <button type="button" aria-label={'Edit draft for '+draft.personName+' on '+draft.date} onClick={()=>{setEditingDraftId(draft.id);setCopyDraft(null);setDraftOpen(true);setDraftError("");}}>Edit</button> <button type="button" aria-label={'Duplicate draft for '+draft.personName+' on '+draft.date} onClick={()=>{setEditingDraftId(null);setCopyDraft({...draft,id:'copy:'+draft.id});setDraftOpen(true);setDraftError('Change the date or time before adding this duplicate draft.');}}>Duplicate</button> <button type="button" aria-label={'Remove draft for '+draft.personName+' on '+draft.date} onClick={()=>{setDrafts(old=>old.filter(d=>d.id!==draft.id));if(editingDraftId===draft.id){setEditingDraftId(null);setDraftOpen(false);}}if(copyDraft?.id==='copy:'+draft.id){setCopyDraft(null);setDraftOpen(false);}}}>Remove</button></li>)}</ul><button type="button" onClick={()=>{setDrafts([]);setEditingDraftId(null);setCopyDraft(null);setDraftOpen(false);}}>Clear demo drafts</button></section>}
    <div className="roster-controls">
      <button type="button" aria-label="Previous week" onClick={()=>{const next=shiftWeek(week,-1);setWeek(next);setSelectedDate(next);setExpandedShift(null);}}>‹</button>
      <strong role="status" aria-live="polite">{days[0].date} – {days[6].date}, {days[6].key.slice(0,4)}</strong>
      <button type="button" aria-label="Next week" onClick={()=>{const next=shiftWeek(week,1);setWeek(next);setSelectedDate(next);setExpandedShift(null);}}>›</button>
      <label className="roster-date-label" htmlFor="roster-date">Jump to date</label><input id="roster-date" type="date" value={selectedDate} onChange={e=>chooseDate(e.target.value)}/>
      <button type="button" onClick={()=>chooseDate(today)}>Today</button>
      <button type="button" onClick={()=>chooseDate(DEMO_WEEK)}>Demo week</button>
    </div>
    <div className="roster-view-switch" role="group" aria-label="Schedule display"><button type="button" aria-pressed={view==='grid'} onClick={()=>{setView('grid');setExpandedShift(null);}}>Weekly grid</button><button type="button" aria-pressed={view==='agenda'} onClick={()=>{setView('agenda');setExpandedShift(null);}}>Daily agenda</button></div>
    {roster && view==='agenda' && <div className="roster-agenda" aria-label={"Shift agenda for "+selectedDate}>{days.map((day,i)=>({day,i})).filter(({day})=>day.key===selectedDate).map(({day,i})=><section className="roster-agenda-day" key={day.key} aria-labelledby={'agenda-'+day.key}><h3 id={'agenda-'+day.key}>{day.day} {day.date}{day.key===today?' · Today':''}</h3><ul>{drafts.filter(draft=>draft.date===day.key).map(draft=><li key={draft.id} className="roster-agenda-draft"><strong>{draft.personName}</strong> · {draft.start}–{draft.end}{draft.overnight?" (+1 day)":""}<small> · Unsaved fictional draft — not published</small></li>)}{roster.filter(person=>person.shifts[i]).map(person=>{const shift=person.shifts[i];const key=rosterShiftKey(person.id,day.key);return <li key={key}><button type="button" className={'roster-agenda-shift '+person.tone} aria-expanded={expandedShift===key} onClick={()=>setExpandedShift(old=>old===key?null:key)}><strong>{person.name}</strong><span>{shift.time}</span><small>{person.role} · Scheduled</small></button>{expandedShift===key&&<p className="roster-shift-detail">{rosterShiftDescription(person,day,shift)}</p>}</li>})}{!roster.some(person=>person.shifts[i])&&!drafts.some(draft=>draft.date===day.key)&&<li className="roster-off">No fictional shifts scheduled or drafted</li>}</ul></section>)}</div>}
    {roster && view==='grid' ? <div className="roster-scroll" role="region" aria-label="Weekly shift grid, scroll horizontally if needed" tabIndex={0}>
      <table className="roster-grid">
        <caption className="sr-only">Fictional weekly roster. Shifts show scheduled hours, not actual presence.</caption>
        <thead><tr><th scope="col">Staff</th>{days.map(d=><th scope="col" key={d.key} className={d.key===today?'roster-today':undefined} aria-current={d.key===today?'date':undefined}>{d.day}<small>{d.date}</small></th>)}</tr></thead>
        <tbody>{roster.map(person=><tr key={person.id}>
          <th scope="row">{person.name}<small>{person.role}</small></th>
          {person.shifts.map((shift,i)=><td key={days[i].key} className={days[i].key===today?'roster-today':undefined}>{shift ? <button type="button" className={'roster-shift roster-grid-shift '+person.tone} aria-expanded={expandedShift===rosterShiftKey(person.id,days[i].key)} aria-controls="roster-grid-detail" onClick={()=>setExpandedShift(old=>old===rosterShiftKey(person.id,days[i].key)?null:rosterShiftKey(person.id,days[i].key))}><strong>{shift.time}</strong><small>Scheduled · Details</small></button> : <span className="roster-off">Off</span>}{drafts.filter(draft=>draft.personId===person.id&&draft.date===days[i].key).map(draft=><div key={draft.id} className="roster-agenda-draft"><strong>{draft.start}–{draft.end}{draft.overnight?' (+1 day)':''}</strong><small>Unsaved fictional draft · not published</small></div>)}</td>)}
        </tr>)}</tbody>
      </table>
      <div id="roster-grid-detail" className="roster-grid-detail" role="status" aria-live="polite">{(()=>{if(!expandedShift)return 'Select a scheduled shift to see its details.';for(const person of roster){for(let i=0;i<days.length;i++){if(person.shifts[i]&&rosterShiftKey(person.id,days[i].key)===expandedShift)return rosterShiftDescription(person,days[i],person.shifts[i]);}}return 'Select a scheduled shift to see its details.';})()}</div>
    </div> : !roster ? <p className="roster-empty" role="status">No fictional roster is available for this week. Actual staffing is unknown.</p> : null}
    <div className="roster-footer"><p>Demo only. Creating and publishing shifts requires the authorized Python roster API.</p><button type="button" className="roster-action" disabled>➤ Publish Schedule</button></div>
  </section>;
}
