export function createVoiceController(env) {
 const store=env.sessionStorage, R=env.SpeechRecognition||env.webkitSpeechRecognition;
 const c={version:3,enabled:false,paused:false,running:false,starting:false,busy:false,speaking:false,blocked:false,failures:0,view:null,pending:null,lastCommand:'',lastTime:0,feedbackId:'',status:'Enable hands-free once after reviewing the audio notice. No button is needed between commands.'};
 c.language=store.getItem('kendrithm-voice-language')||'en-IN'; c.wakeRequired=store.getItem('kendrithm-wake-word')!=='off'; c.spoken=store.getItem('kendrithm-spoken-feedback')!=='no';
 c.paint=()=>{if(c.view){c.view.status.textContent=c.status;c.view.start.disabled=!R||(c.enabled&&!c.blocked);c.view.stop.disabled=!c.enabled;c.view.mode.textContent=c.paused?'Commands paused · microphone on':c.running?'Microphone on':c.enabled?'Connecting microphone':'Microphone off';}};
 c.setStatus=t=>{c.status=t;c.paint();};
 c.schedule=(delay=600)=>{env.clearTimeout(c.timer);if(c.enabled&&!c.blocked&&!c.busy&&!c.speaking)c.timer=env.setTimeout(()=>c.start(),delay);};
 c.start=()=>{if(!R||!c.enabled||c.blocked||c.running||c.starting||c.busy||c.speaking)return;try{c.starting=true;c.recognition.lang=c.language;c.recognition.start();}catch(e){c.starting=false;c.blocked=true;c.setStatus('Browser activation is required. Enable hands-free once to reconnect.');}};
 c.enable=consent=>{if(!consent){c.setStatus('Accept the continuous microphone and browser speech-service notice first.');return;}c.enabled=true;c.blocked=false;c.failures=0;c.paused=false;c.start();c.paint();};
 c.disable=()=>{c.enabled=false;c.starting=false;c.busy=false;c.speaking=false;env.clearTimeout(c.timer);env.clearTimeout(c.busyTimer);env.clearTimeout(c.speechTimer);c.recognition?.abort();env.speechSynthesis?.cancel();c.setStatus('Microphone off. Enable hands-free once to restart; voice cannot resume while the microphone is off.');};
 c.changeLanguage=v=>{c.language=v;store.setItem('kendrithm-voice-language',v);c.recognition?.abort();c.schedule();};
 c.flush=()=>{if(c.pending&&c.view){const p=c.pending;c.pending=null;c.view.emit('command',p);}};
 c.command=transcript=>{
  let text=transcript.trim();if(!text||c.speaking||c.busy||!c.enabled)return;if(c.view)c.view.transcript.textContent=text;
  const wake=text.match(/^(?:hey\s+)?(?:kendrithm|kendritham|kendra\s+rhythm|கேந்திரிதம்|கேந்திரம்)[\s,:-]*(.*)$/iu);
  if(wake)text=wake[1].trim();else if(c.wakeRequired||c.paused)return;
  if(!text){c.setStatus('Ready. Say your command after Kendrithm.');return;}
  const normal=text.toLowerCase().replace(/[.!?]+$/,'').trim();
  if(['stop listening','microphone off','turn off microphone'].includes(normal)){c.disable();return;}
  if(['pause commands','go to sleep'].includes(normal)){c.paused=true;c.setStatus('Commands paused. Microphone stays on for Kendrithm resume commands.');return;}
  if(['resume','resume commands','wake up'].includes(normal)){c.paused=false;c.setStatus('Listening continuously. Say Kendrithm followed by a command.');return;}
  if(c.paused)return;
  const time=env.Date.now();if(normal===c.lastCommand&&time-c.lastTime<1800)return;
  c.lastCommand=normal;c.lastTime=time;c.busy=true;c.pending={id:env.crypto.randomUUID(),text};c.setStatus('Processing: '+text);c.recognition?.abort();c.flush();
  env.clearTimeout(c.busyTimer);c.busyTimer=env.setTimeout(()=>{if(c.busy){c.busy=false;c.setStatus('No app response yet. Listening again; check before repeating the command.');c.schedule();}},15000);
 };
 c.feedback=data=>{
  if(!data?.feedbackId||data.feedbackId===c.feedbackId)return;c.feedbackId=data.feedbackId;c.busy=false;env.clearTimeout(c.busyTimer);c.setStatus(data.feedback+(c.enabled?' Listening will continue.':''));
  if(c.spoken&&c.enabled&&env.speechSynthesis){c.speaking=true;c.recognition?.abort();const u=new env.SpeechSynthesisUtterance(data.feedback);u.lang=c.language;const done=()=>{env.clearTimeout(c.speechTimer);c.speaking=false;c.schedule();};u.onend=done;u.onerror=done;env.speechSynthesis.cancel();env.speechSynthesis.speak(u);c.speechTimer=env.setTimeout(done,25000);}else c.schedule();
 };
 if(!R){c.blocked=true;c.setStatus('Continuous speech recognition is unavailable here. Try Chrome or Edge.');}
 else{
  c.recognition=new R();c.recognition.continuous=true;c.recognition.interimResults=true;c.recognition.maxAlternatives=1;
  c.recognition.onstart=()=>{c.starting=false;c.running=true;c.setStatus(c.paused?'Commands paused · microphone listening for resume.':'Hands-free listening. Say Kendrithm followed by a command.');};
  c.recognition.onend=()=>{c.starting=false;c.running=false;c.paint();c.schedule();};
  c.recognition.onerror=e=>{if(['aborted','no-speech'].includes(e.error))return;c.failures++;if(['not-allowed','service-not-allowed','audio-capture'].includes(e.error)||c.failures>=3){c.blocked=true;c.setStatus(e.error==='not-allowed'?'Microphone permission or browser activation required. Allow microphone access and enable hands-free once.':e.error==='audio-capture'?'No microphone found. Check your input device.':'Browser speech service unavailable. Reconnection stopped after errors; try Chrome or Edge.');}else c.setStatus('Speech interrupted. Reconnecting automatically…');};
  c.recognition.onresult=e=>{for(let i=e.resultIndex;i<e.results.length;i++){const r=e.results[i];if(r.isFinal){c.failures=0;c.command(r[0].transcript);}else if(c.view)c.view.transcript.textContent=r[0].transcript;}};
 }
 return c;
}
export default function(component){
 const env=window;
 if(!env.__kendrithmVoice||env.__kendrithmVoice.version!==3){env.__kendrithmVoice?.disable();env.__kendrithmVoice=createVoiceController(env);env.addEventListener('pagehide',()=>env.__kendrithmVoice.disable());}
 const c=env.__kendrithmVoice,root=component.parentElement;
 const view={status:root.querySelector('#voice-status'),transcript:root.querySelector('#voice-transcript'),mode:root.querySelector('#voice-mode'),start:root.querySelector('#voice-start'),stop:root.querySelector('#voice-stop'),emit:component.setTriggerValue};c.view=view;
 const language=root.querySelector('#voice-language'),spoken=root.querySelector('#voice-spoken'),wake=root.querySelector('#voice-wake'),consent=root.querySelector('#voice-consent');
 language.value=c.language;spoken.checked=c.spoken;wake.checked=c.wakeRequired;consent.checked=c.enabled;
 view.start.onclick=()=>c.enable(consent.checked);view.stop.onclick=()=>c.disable();consent.onchange=()=>{if(!consent.checked)c.disable();};language.onchange=()=>c.changeLanguage(language.value);
 spoken.onchange=()=>{c.spoken=spoken.checked;env.sessionStorage.setItem('kendrithm-spoken-feedback',c.spoken?'yes':'no');};wake.onchange=()=>{c.wakeRequired=wake.checked;env.sessionStorage.setItem('kendrithm-wake-word',c.wakeRequired?'on':'off');};
 c.paint();c.feedback(component.data);c.flush();c.schedule();
 return ()=>{if(c.view===view)c.view=null;};
}
