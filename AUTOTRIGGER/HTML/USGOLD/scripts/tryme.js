let stream = null;
let currentOverlayUrl = '';

export async function openTryMe(overlayUrl) {
  currentOverlayUrl = overlayUrl || '';
  const m = document.getElementById('tryme-modal');
  const v = document.getElementById('tryme-video');
  const o = document.getElementById('tryme-overlay');
  o.src = currentOverlayUrl;
  m.classList.remove('hidden');
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' }, audio: false });
    v.srcObject = stream;
  } catch {}
}

export function closeTryMe() {
  const m = document.getElementById('tryme-modal');
  m.classList.add('hidden');
  const v = document.getElementById('tryme-video');
  if (stream) {
    stream.getTracks().forEach(t => t.stop());
    stream = null;
  }
  v.srcObject = null;
}

export function initTryMeControls() {
  const o = document.getElementById('tryme-overlay');
  const scale = document.getElementById('overlay-scale');
  const vy = document.getElementById('overlay-y');
  scale.addEventListener('input', () => {
    o.style.width = `${scale.value}%`;
  });
  vy.addEventListener('input', () => {
    o.style.bottom = `${10 + Number(vy.value) / 2}%`;
  });
}
