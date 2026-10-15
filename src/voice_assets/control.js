export default function(component) {
  const {parentElement, setTriggerValue, data} = component;
  const start = parentElement.querySelector('#voice-start');
  const stop = parentElement.querySelector('#voice-stop');
  const status = parentElement.querySelector('#voice-status');
  const transcript = parentElement.querySelector('#voice-transcript');
  const language = parentElement.querySelector('#voice-language');
  const spoken = parentElement.querySelector('#voice-spoken');
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  let recognition = null;
  language.value = sessionStorage.getItem('kendrithm-voice-language') || 'en-IN';
  language.onchange = () => sessionStorage.setItem('kendrithm-voice-language',language.value);
  spoken.checked = sessionStorage.getItem('kendrithm-spoken-feedback') === 'yes';
  spoken.onchange = () => sessionStorage.setItem('kendrithm-spoken-feedback',spoken.checked ? 'yes':'no');
  if (!Recognition) {
    start.disabled = true;
    status.textContent = 'Speech recognition is unavailable in this browser. Open this app in Chrome or Edge, or use the typed command below.';
  } else {
    recognition = new Recognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;
    recognition.onstart = () => { status.textContent='Listening… Speak one command.'; start.disabled=true; stop.disabled=false; };
    recognition.onend = () => { start.disabled=false; stop.disabled=true; if(status.textContent.startsWith('Listening')) status.textContent='Stopped. Press Listen to try again.'; };
    recognition.onerror = (event) => {
      const messages = {
        'not-allowed':'Microphone access was denied. Allow the microphone in your browser settings, then try again.',
        'service-not-allowed':'This browser cannot use its speech service here. Try Chrome or Edge.',
        'network':'Your browser speech service could not connect. Try Chrome or Edge with an internet connection.',
        'audio-capture':'No microphone is available. Check your input device.',
        'no-speech':'No speech detected. Press Listen and try again.',
        'aborted':'Listening stopped.'
      };
      status.textContent=messages[event.error] || 'Speech recognition failed. Please try again.';
    };
    recognition.onresult = (event) => {
      let finalText='', interim='';
      for(let i=event.resultIndex;i<event.results.length;i++) {
        if(event.results[i].isFinal) finalText+=event.results[i][0].transcript;
        else interim+=event.results[i][0].transcript;
      }
      transcript.textContent=finalText || interim;
      if(finalText.trim()) {
        recognition.stop();
        status.textContent='Processing command…';
        setTriggerValue('command',{id:crypto.randomUUID(),text:finalText.trim()});
      }
    };
    start.onclick=()=>{ try { window.speechSynthesis?.cancel(); recognition.lang=language.value; transcript.textContent=''; recognition.start(); } catch(error) {status.textContent='Listening could not start. Stop and try again.';} };
    stop.onclick=()=>recognition.abort();
  }
  if(data?.feedback) status.textContent=data.feedback;
  if(data?.feedbackId && spoken.checked && window.speechSynthesis && sessionStorage.getItem('kendrithm-last-spoken')!==data.feedbackId) {
    sessionStorage.setItem('kendrithm-last-spoken',data.feedbackId);
    const utterance=new SpeechSynthesisUtterance(data.feedback);
    utterance.lang='en-IN';
    window.speechSynthesis.speak(utterance);
  }
  return ()=>{ if(recognition) {recognition.onresult=null; recognition.onend=null; recognition.onerror=null; recognition.abort();} };
}

