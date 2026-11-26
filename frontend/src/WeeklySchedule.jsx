import React,{useState} from 'react';
import {DEMO_WEEK,shiftWeek,weekDays,demoRoster,weekForDate} from './demoRoster.js';
import './weeklySchedule.css';

export default function WeeklySchedule(){
  const [week,setWeek] = useState(DEMO_WEEK);
  const [selectedDate,setSelectedDate] = useState(DEMO_WEEK);
  const [view,setView] = useState('grid');
  const [expandedShift,setExpandedShift] = useState(null);
  const todayParts = Object.fromEntries(new Intl.DateTimeFormat('en-GB',{timeZone:'Europe/Brussels',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date()).filter(p=>p.type!=='literal').map(p=>[p.type,p.value]));
  const today = `${todayParts.year}-${todayParts.month}-${todayParts.day}`;
  function chooseDate(value){if(!/^\d{4}-\d{2}-\d{2}$/.test(value))return;setSelectedDate(value);setWeek(weekForDate(value));}
  const days = weekDays(week);
  const roster = demoRoster(week);
  return <section className="roster-panel" aria-labelledby="roster-title">
    <div className="roster-heading">
      <div><h2 id="roster-title">Weekly Schedule</h2><p>Fictional roster · Europe/Brussels · planned shifts only</p></div>
      <button type="button" className="roster-action" disabled>+ Create Shift</button>
    </div>
    <div className="roster-controls">
      <button type="button" aria-label="Previous week" onClick={()=>{const next=shiftWeek(week,-1);setWeek(next);setSelectedDate(next);}}>‹</button>
      <strong role="status" aria-live="polite">{days[0].date} – {days[6].date}, {days[6].key.slice(0,4)}</strong>
      <button type="button" aria-label="Next week" onClick={()=>{const next=shiftWeek(week,1);setWeek(next);setSelectedDate(next);}}>›</button>
      <label className="roster-date-label" htmlFor="roster-date">Jump to date</label><input id="roster-date" type="date" value={selectedDate} onChange={e=>chooseDate(e.target.value)}/>
      <button type="button" onClick={()=>chooseDate(today)}>Today</button>
      <button type="button" onClick={()=>chooseDate(DEMO_WEEK)}>Demo week</button>
    </div>
    <div className="roster-view-switch" role="group" aria-label="Schedule display"><button type="button" aria-pressed={view==='grid'} onClick={()=>{setView('grid');setExpandedShift(null);}}>Weekly grid</button><button type="button" aria-pressed={view==='agenda'} onClick={()=>{setView('agenda');setExpandedShift(null);}}>Daily agenda</button></div>
    {roster && view==='agenda' && <div className="roster-agenda" aria-label="Daily shift agenda">{days.map((day,i)=><section className="roster-agenda-day" key={day.key} aria-labelledby={'agenda-'+day.key}><h3 id={'agenda-'+day.key}>{day.day} {day.date}{day.key===today?' · Today':''}</h3><ul>{roster.filter(person=>person.shifts[i]).map(person=>{const shift=person.shifts[i];const key=person.id+'-'+day.key;return <li key={key}><button type="button" className={'roster-agenda-shift '+person.tone} aria-expanded={expandedShift===key} onClick={()=>setExpandedShift(old=>old===key?null:key)}><strong>{person.name}</strong><span>{shift.time}</span><small>{person.role} · Scheduled</small></button>{expandedShift===key&&<p className="roster-shift-detail">Fictional planned shift for {person.name} ({person.role}) on {day.date}. Hours: {shift.time}. Actual attendance is unknown. No changes are saved.</p>}</li>})}{!roster.some(person=>person.shifts[i])&&<li className="roster-off">No fictional shifts scheduled</li>}</ul></section>)}</div>}
    {roster && view==='grid' ? <div className="roster-scroll" role="region" aria-label="Weekly shift grid, scroll horizontally if needed" tabIndex={0}>
      <table className="roster-grid">
        <caption className="sr-only">Fictional weekly roster. Shifts show scheduled hours, not actual presence.</caption>
        <thead><tr><th scope="col">Staff</th>{days.map(d=><th scope="col" key={d.key} className={d.key===today?'roster-today':undefined} aria-current={d.key===today?'date':undefined}>{d.day}<small>{d.date}</small></th>)}</tr></thead>
        <tbody>{roster.map(person=><tr key={person.id}>
          <th scope="row">{person.name}<small>{person.role}</small></th>
          {person.shifts.map((shift,i)=><td key={days[i].key} className={days[i].key===today?'roster-today':undefined}>{shift ? <div className={'roster-shift '+person.tone}><strong>{shift.time}</strong><small>Scheduled</small></div> : <span className="roster-off">Off</span>}</td>)}
        </tr>)}</tbody>
      </table>
    </div> : !roster ? <p className="roster-empty" role="status">No fictional roster is available for this week. Actual staffing is unknown.</p> : null}
    <div className="roster-footer"><p>Demo only. Creating and publishing shifts requires the authorized Python roster API.</p><button type="button" className="roster-action" disabled>➤ Publish Schedule</button></div>
  </section>;
}
