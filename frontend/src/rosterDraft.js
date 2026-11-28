/** Synthetic browser-memory shift drafts. No server persistence, authorization or schedule validation. */
const datePattern=/^\d{4}-\d{2}-\d{2}$/;
const timePattern=/^([01]\d|2[0-3]):[0-5]\d$/;
export function createDemoShiftDraft(input,people,existing=[]){
  if(!input||typeof input!=='object')throw new TypeError('Missing shift draft');
  const {personId,date,start,end}=input;
  if(typeof date!=='string'||!datePattern.test(date))throw new TypeError('Choose a valid date');
  const parsed=new Date(date+'T12:00:00Z');
  if(!Number.isFinite(parsed.getTime())||parsed.toISOString().slice(0,10)!==date)throw new TypeError('Choose a valid date');
  if(!timePattern.test(start)||!timePattern.test(end)||start===end)throw new TypeError('Choose distinct valid start and end times');
  const person=Array.isArray(people)&&people.find(p=>p.id===personId);
  if(!person)throw new TypeError('Select a fictional employee');
  if(existing.some(d=>d.personId===personId&&d.date===date&&d.start===start&&d.end===end))throw new TypeError('Identical draft already exists');
  const id=[personId,date,start,end].join(':');
  return {id,personId,personName:person.name,date,start,end,overnight:end<start,source:'synthetic-draft'};
}

/** Atomically replace a browser-only draft after validating against other drafts. */
export function replaceDemoShiftDraft(drafts,id,input,people){
  if(!Array.isArray(drafts)||typeof id!=='string')throw new TypeError('Invalid draft selection');
  const index=drafts.findIndex(d=>d.id===id);
  if(index<0)throw new TypeError('Draft no longer exists');
  const updated=createDemoShiftDraft(input,people,drafts.filter(d=>d.id!==id));
  return drafts.map((draft,i)=>i===index?updated:draft);
}
