/** Fictional checklist state only. Never represents Python SOP evidence or completion. */
export const initialDemoTasks = Object.freeze([
  Object.freeze({name:'Check refrigeration log',done:false}),
  Object.freeze({name:'Sanitize prep stations',done:true}),
  Object.freeze({name:'Review closing checklist',done:false})
]);

export function resetDemoTasks(){
  return initialDemoTasks.map(task=>({...task}));
}

export function toggleDemoTask(tasks,index){
  if(!Array.isArray(tasks)||!Number.isInteger(index)||index<0||index>=tasks.length)return tasks;
  return tasks.map((task,i)=>i===index?{...task,done:!task.done}:task);
}
