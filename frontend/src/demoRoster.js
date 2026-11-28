// Fictional roster snapshots only. No attendance, authorization or persistence logic.
export const DEMO_WEEK = '2026-11-23';
const NEXT_WEEK = '2026-11-30';
const people = [
  {id:'sofia',name:'Sofia',role:'Floor lead',tone:'green',time:'11:00–19:00',days:[0,1,3,4,5]},
  {id:'noah',name:'Noah',role:'Chef',tone:'blue',time:'12:00–22:00',days:[1,2,3,4,5]},
  {id:'mila',name:'Mila',role:'Bartender',tone:'gold',time:'16:00–23:00',days:[0,3,4,5,6]},
  {id:'liam',name:'Liam',role:'Server',tone:'cyan',time:'11:00–19:00',days:[0,1,2,5,6]},
];
export function shiftWeek(week, offset) {
  const date = new Date(`${week}T12:00:00Z`);
  date.setUTCDate(date.getUTCDate() + 7 * offset);
  return date.toISOString().slice(0,10);
}
export function weekDays(week) {
  return Array.from({length:7}, (_,i) => {
    const date = new Date(`${week}T12:00:00Z`);
    date.setUTCDate(date.getUTCDate()+i);
    return {key:date.toISOString().slice(0,10),day:new Intl.DateTimeFormat('en-BE',{weekday:'short',timeZone:'UTC'}).format(date),date:new Intl.DateTimeFormat('en-BE',{day:'numeric',month:'short',timeZone:'UTC'}).format(date)};
  });
}
export function demoRoster(week) {
  if (week !== DEMO_WEEK && week !== NEXT_WEEK) return null;
  return people.map(({days,time,...person},index) => ({...person,shifts:Array.from({length:7},(_,day) => {
    const planned = days.includes(week === NEXT_WEEK ? (day+1)%7 : day);
    return planned ? {time:week === NEXT_WEEK && index === 2 ? '18:00–01:00 (+1 day)' : time} : null;
  })}));
}

// Calendar selection is a display concern, never a scheduling authority.
export function weekForDate(value) {
  if(typeof value!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(value))throw new TypeError('Invalid calendar date');
  const date=new Date(value+'T12:00:00Z');
  if(!Number.isFinite(date.getTime())||date.toISOString().slice(0,10)!==value)throw new TypeError('Invalid calendar date');
  const mondayOffset=(date.getUTCDay()+6)%7;
  date.setUTCDate(date.getUTCDate()-mondayOffset);
  return date.toISOString().slice(0,10);
}
