import { getRates, setRates } from './services/prices.js';
import { getProducts, setProducts } from './services/products.js';
import { showToast } from './ui.js';

const authKey = 'usg_admin_auth';
const defaultCred = { username: 'admin', password: 'admin123' };
let projectDirHandle = null;
let dataDirHandle = null;
let imagesDirHandle = null;
let productsFileHandle = null;
async function ensureFsSetup() {
  if (imagesDirHandle && productsFileHandle) return;
  const dir = await window.showDirectoryPicker();
  let root = dir;
  try { root = await dir.getDirectoryHandle('USGOLD'); } catch {}
  dataDirHandle = await root.getDirectoryHandle('data', { create: true });
  imagesDirHandle = await dataDirHandle.getDirectoryHandle('images', { create: true });
  productsFileHandle = await dataDirHandle.getFileHandle('products.json', { create: true });
}
function dataUrlToBlob(dataUrl) {
  const parts = dataUrl.split(',');
  const meta = parts[0];
  const b64 = parts[1];
  const mime = meta.substring(meta.indexOf(':') + 1, meta.indexOf(';'));
  const bin = atob(b64);
  const len = bin.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) bytes[i] = bin.charCodeAt(i);
  return new Blob([bytes], { type: mime });
}
async function resolveImageBlob(fileInput, urlOrData) {
  const file = fileInput.files && fileInput.files[0] ? fileInput.files[0] : null;
  if (file) return file;
  if (!urlOrData) return null;
  if (urlOrData.startsWith('data:')) return dataUrlToBlob(urlOrData);
  if (urlOrData.startsWith('http')) {
    const res = await fetch(urlOrData);
    if (!res.ok) return null;
    return await res.blob();
  }
  return null;
}

function getCred() {
  try {
    const raw = localStorage.getItem('usg_admin_cred');
    return raw ? JSON.parse(raw) : defaultCred;
  } catch {
    return defaultCred;
  }
}

function setHome(data) {
  const prev = JSON.parse(localStorage.getItem('usg_home') || '{}');
  localStorage.setItem('usg_home', JSON.stringify({ ...prev, ...data }));
}
function getHome() {
  try {
    return JSON.parse(localStorage.getItem('usg_home') || '{}');
  } catch { return {}; }
}
function setContact(data) {
  const prev = JSON.parse(localStorage.getItem('usg_contact') || '{}');
  localStorage.setItem('usg_contact', JSON.stringify({ ...prev, ...data }));
}
function getContact() {
  try {
    return JSON.parse(localStorage.getItem('usg_contact') || '{}');
  } catch { return {}; }
}

function renderProductsAdmin(list) {
  const grid = document.getElementById('products-list');
  const section = document.getElementById('products-list-section');
  section.classList.remove('hidden');
  grid.innerHTML = '';
  list.forEach(p => {
    const el = document.createElement('div');
    el.className = 'card';
    el.innerHTML = `
      <div class="card-media">
        <img src="${p.imageUrl}" alt="${p.name}">
      </div>
      <div class="card-content">
        <div class="title-row">
          <div class="title">${p.name}</div>
          <div class="meta">${p.id}</div>
        </div>
        <div class="price-row">
          <div>${p.metal} • ${p.category} • ${p.gender}</div>
          <div class="meta">${p.weightGrams} g</div>
        </div>
      </div>
      <div class="actions-row">
        <button class="btn sm" data-action="edit">Edit</button>
        <button class="btn sm" data-action="delete">Delete</button>
      </div>
    `;
    el.querySelector('[data-action="edit"]').addEventListener('click', () => {
      document.getElementById('prod-id').value = p.id;
      document.getElementById('prod-name').value = p.name;
      document.getElementById('prod-metal').value = p.metal;
      document.getElementById('prod-category').value = p.category;
      document.getElementById('prod-gender').value = p.gender;
      document.getElementById('prod-weight').value = p.weightGrams;
      document.getElementById('prod-image').value = p.imageUrl;
      document.getElementById('prod-desc').value = p.description;
      updateImagePreview(p.imageUrl);
      document.getElementById('add-product').textContent = 'Update Product';
      document.getElementById('products-admin').scrollIntoView({ behavior: 'smooth' });
    });
    el.querySelector('[data-action="delete"]').addEventListener('click', async () => {
      const next = (await getProducts()).filter(x => x.id !== p.id);
      setProducts(next);
      renderProductsAdmin(next);
      showToast('Product deleted');
    });
    grid.appendChild(el);
  });
}

function initLogin() {
  const btn = document.getElementById('admin-login');
  btn.addEventListener('click', () => {
    const u = document.getElementById('admin-username').value.trim();
    const pw = document.getElementById('admin-password').value.trim();
    const cred = getCred();
    const ok = u === cred.username && pw === cred.password;
    if (!ok) { showToast('Invalid credentials'); return; }
    localStorage.setItem(authKey, '1');
    document.getElementById('login-section').classList.add('hidden');
    document.getElementById('dashboard').classList.remove('hidden');
    document.getElementById('products-admin').classList.remove('hidden');
    document.getElementById('products-admin-header').classList.remove('hidden');
    hydrateForms();
    getProducts().then(renderProductsAdmin);
  });
}

function hydrateForms() {
  const r = getRates();
  document.getElementById('rate-gold').value = r.gold;
  document.getElementById('rate-silver').value = r.silver;
  document.getElementById('rate-currency').value = r.currency || 'INR';
  const h = getHome();
  document.getElementById('hero-title').value = h.heroTitle || '';
  document.getElementById('hero-subtitle').value = h.heroSubtitle || '';
  const c = getContact();
  document.getElementById('contact-phone-input').value = c.phone || '';
  document.getElementById('contact-whatsapp-input').value = c.whatsapp || '';
}

function initRatesForm() {
  document.getElementById('save-rates').addEventListener('click', () => {
    const gold = Number(document.getElementById('rate-gold').value);
    const silver = Number(document.getElementById('rate-silver').value);
    const currency = document.getElementById('rate-currency').value;
    setRates({ gold, silver, currency, lastUpdated: null }); // Clear live status on manual override
    showToast('Rates updated manually');
  });
}

function initHomeContactForm() {
  document.getElementById('save-home-contact').addEventListener('click', () => {
    const heroTitle = document.getElementById('hero-title').value.trim();
    const heroSubtitle = document.getElementById('hero-subtitle').value.trim();
    setHome({ heroTitle, heroSubtitle });
    const phone = document.getElementById('contact-phone-input').value.trim();
    const whatsapp = document.getElementById('contact-whatsapp-input').value.trim();
    setContact({ phone, whatsapp });
    showToast('Home & contact saved');
  });
}

function updateImagePreview(url) {
  const preview = document.getElementById('image-preview');
  const img = preview.querySelector('img');
  if (url) {
    img.src = url;
    preview.classList.remove('hidden');
  } else {
    preview.classList.add('hidden');
    img.src = '';
  }
}

function initProductForm() {
  const clearBtn = document.getElementById('clear-form');
  const addBtn = document.getElementById('add-product');
  const fileInput = document.getElementById('prod-image-file');
  const hiddenInput = document.getElementById('prod-image');
  const removeImgBtn = document.getElementById('remove-image');

  fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (ev) => {
        const base64 = ev.target.result;
        hiddenInput.value = base64;
        updateImagePreview(base64);
      };
      reader.readAsDataURL(file);
    }
  });

  removeImgBtn.addEventListener('click', () => {
    hiddenInput.value = '';
    fileInput.value = '';
    updateImagePreview('');
  });
  
  const clear = () => {
    document.getElementById('prod-id').value = '';
    document.getElementById('prod-name').value = '';
    document.getElementById('prod-weight').value = '';
    document.getElementById('prod-image').value = '';
    document.getElementById('prod-image-file').value = '';
    updateImagePreview('');
    document.getElementById('prod-desc').value = '';
    addBtn.textContent = 'Save Product';
  };

  clearBtn.addEventListener('click', clear);

  addBtn.addEventListener('click', async () => {
    const p = {
      id: document.getElementById('prod-id').value.trim(),
      name: document.getElementById('prod-name').value.trim(),
      metal: document.getElementById('prod-metal').value,
      category: document.getElementById('prod-category').value,
      gender: document.getElementById('prod-gender').value,
      weightGrams: Number(document.getElementById('prod-weight').value),
      imageUrl: document.getElementById('prod-image').value.trim(),
      description: document.getElementById('prod-desc').value.trim(),
    };
    if (!p.id || !p.name) { showToast('ID and Name required'); return; }
    let blob = null;
    try { blob = await resolveImageBlob(fileInput, p.imageUrl); } catch {}
    if (blob) {
      try {
        await ensureFsSetup();
        const t = blob.type || 'image/jpeg';
        const ext = t.indexOf('png') >= 0 ? 'png' : (t.indexOf('webp') >= 0 ? 'webp' : 'jpg');
        const unique = (globalThis.crypto && crypto.randomUUID) ? crypto.randomUUID() : Date.now().toString();
        const fname = `${p.id}-${unique}.${ext}`;
        const fh = await imagesDirHandle.getFileHandle(fname, { create: true });
        const w = await fh.createWritable();
        await w.write(blob);
        await w.close();
        p.imageUrl = `data/images/${fname}`;
      } catch {}
    }
    const list = await getProducts();
    const exists = list.findIndex(x => x.id === p.id);
    if (exists >= 0) {
      list[exists] = p;
      showToast('Product updated');
    } else {
      list.push(p);
      showToast('Product added');
    }
    setProducts(list);
    try {
      await ensureFsSetup();
      const w = await productsFileHandle.createWritable();
      await w.write(JSON.stringify(list, null, 2));
      await w.close();
    } catch {}
    renderProductsAdmin(list);
    clear();
  });
}

function boot() {
  initLogin();
  initRatesForm();
  initHomeContactForm();
  initProductForm();
}

boot();
