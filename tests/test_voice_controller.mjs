import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const code=await readFile(new URL('../src/voice_assets/control.js',import.meta.url),'utf8');
const {createVoiceController}=await import('data:text/javascript;base64,'+Buffer.from(code).toString('base64'));
function setup(){
 const timers=new Map();let id=0;const emitted=[];const spoken=[];
 class Recognition{start(){this.starts=(this.starts||0)+1;this.onstart?.();}abort(){this.aborts=(this.aborts||0)+1;this.onend?.();}}
 const env={SpeechRecognition:Recognition,sessionStorage:{getItem:()=>null,setItem:()=>{}},Date:{now:()=>10000},crypto:{randomUUID:()=>String(++id)},setTimeout:(f,delay)=>{const i=++id;timers.set(i,{f,delay});return i;},clearTimeout:i=>timers.delete(i),SpeechSynthesisUtterance:class{constructor(t){this.text=t;}},speechSynthesis:{cancel(){},speak(u){spoken.push(u);}}};
 const c=createVoiceController(env);c.view={status:{},transcript:{},mode:{},start:{},stop:{},emit:(...args)=>emitted.push(args)};
 const tick=()=>{const i=[...timers].find(([,t])=>t.delay===600)?.[0];if(i){const f=timers.get(i).f;timers.delete(i);f();}};
 return {c,env,timers,emitted,spoken,tick};
}
test('microphone is off until explicit consent and activation',()=>{const {c}=setup();c.schedule();assert.equal(c.recognition.starts,undefined);c.enable(false);assert.equal(c.recognition.starts,undefined);c.enable(true);assert.equal(c.recognition.starts,1);assert.equal(c.recognition.continuous,true);});
test('silence restarts automatically without button presses',()=>{const {c,tick}=setup();c.enable(true);c.recognition.onend();tick();assert.equal(c.recognition.starts,2);});
test('wake word gates commands and feedback resumes listening',()=>{const {c,emitted,spoken,tick}=setup();c.enable(true);c.command('show my leads');assert.equal(emitted.length,0);c.command('Kendrithm, show my leads');assert.equal(emitted.length,1);assert.equal(emitted[0][1].text,'show my leads');c.feedback({feedbackId:'1',feedback:'Opened leads'});assert.equal(c.speaking,true);c.command('Kendrithm start mission');assert.equal(emitted.length,1);spoken[0].onend();tick();assert.equal(c.running,true);});
test('pause and resume work by voice without stopping microphone',()=>{const {c,emitted}=setup();c.enable(true);c.command('Kendrithm pause commands');assert.equal(c.paused,true);assert.equal(c.running,true);c.command('Kendrithm start research');assert.equal(emitted.length,0);c.command('Kendrithm resume commands');assert.equal(c.paused,false);c.command('Kendrithm show my leads');assert.equal(emitted.length,1);});
test('microphone off stops automatic restarts',()=>{const {c,tick}=setup();c.enable(true);c.command('Kendrithm stop listening');tick();assert.equal(c.enabled,false);assert.equal(c.running,false);assert.equal(c.recognition.starts,1);});
test('permission failure blocks retry loops',()=>{const {c,tick}=setup();c.enable(true);c.recognition.onerror({error:'not-allowed'});c.recognition.onend();tick();assert.equal(c.blocked,true);assert.equal(c.recognition.starts,1);});
test('replacing the view preserves microphone and emits to new view',()=>{const {c,emitted}=setup();c.enable(true);c.view=null;assert.equal(c.running,true);c.command('Kendrithm mission status');assert.equal(emitted.length,0);c.view={status:{},transcript:{},mode:{},start:{},stop:{},emit:(...a)=>emitted.push(a)};c.flush();assert.equal(emitted.length,1);});
