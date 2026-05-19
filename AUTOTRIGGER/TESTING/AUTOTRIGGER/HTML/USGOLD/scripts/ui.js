import { formatCurrency, getRates, rateForMetal } from './services/prices.js';
import { addToWishlist, removeFromWishlist, getWishlist } from './wishlist.js';
import { openTryMe } from './tryme.js';

export function renderRates() {
  const r = getRates();
  const g1 = document.getElementById('gold-1g');
  const g10 = document.getElementById('gold-10g');
  const s1 = document.getElementById('silver-1g');
  const s10 = document.getElementById('silver-10g');
  
  const goldRate = r.gold; // This is 22K per gram
  const silverRate = r.silver; // This is per gram

  g1.textContent = formatCurrency(goldRate, r.currency);
  g10.textContent = formatCurrency(goldRate * 10, r.currency);
  s1.textContent = formatCurrency(silverRate, r.currency);
  s10.textContent = formatCurrency(silverRate * 10, r.currency);

  // Live status update
  let statusEl = document.getElementById('rate-status-msg');
  if (!statusEl) {
    statusEl = document.createElement('div');
    statusEl.id = 'rate-status-msg';
    statusEl.style.cssText = 'grid-column: 1 / -1; text-align: center; font-size: 0.85rem; margin-top: -8px; opacity: 0.8;';
    document.querySelector('.hero-rates').appendChild(statusEl);
  }

  if (r.lastUpdated) {
    const d = new Date(r.lastUpdated);
    const time = d.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    statusEl.innerHTML = `<span style="color: #27ae60; font-weight: bold;">● Live Market Rates</span> <span style="color: var(--muted);">(Updated ${time})</span>`;
  } else {
    statusEl.textContent = 'Estimated Market Rates';
    statusEl.style.color = 'var(--muted)';
  }
}

export function renderProducts(list) {
  const grid = document.getElementById('products-grid');
  grid.innerHTML = '';
  const rates = getRates();
  list.forEach(p => {
    const est = rateForMetal(p.metal) * p.weightGrams;
    const el = document.createElement('div');
    el.className = 'card';
    el.innerHTML = `
      <div class="card-media">
        <img src="${p.imageUrl}" alt="${p.name}">
        <div class="hover-info">
          <div class="hi-line"><span>${p.name}</span><span>${p.weightGrams} g</span></div>
          <div class="hi-line"><span>${p.metal.toUpperCase()} rate</span><span>${formatCurrency(rateForMetal(p.metal), rates.currency)}</span></div>
          <div class="hi-line"><span>Estimated price</span><span>${formatCurrency(est, rates.currency)}</span></div>
          <div class="hi-line">${p.description}</div>
        </div>
      </div>
      <div class="card-content">
        <div class="title-row">
          <div class="title">${p.name}</div>
          <div class="meta">${p.category} • ${p.gender}</div>
        </div>
        <div class="price-row">
          <div>${formatCurrency(est, rates.currency)}</div>
          <div class="meta">${p.weightGrams} g</div>
        </div>
      </div>
      <div class="actions-row">
        <button class="btn sm" data-action="enquire">Enquire / Buy</button>
        <button class="btn sm" data-action="wishlist">Wishlist</button>
        <button class="btn sm" data-action="tryme">Try Me</button>
      </div>
    `;
    el.querySelector('[data-action="enquire"]').addEventListener('click', () => openEnquiry(p));
    el.querySelector('[data-action="wishlist"]').addEventListener('click', () => {
      addToWishlist(p);
      showToast('Added to wishlist');
      renderWishlist();
    });
    el.querySelector('[data-action="tryme"]').addEventListener('click', () => {
      const overlay = p.imageUrl;
      openTryMe(overlay);
    });
    grid.appendChild(el);
  });
}

export function renderWishlist() {
  const list = getWishlist();
  const section = document.getElementById('wishlist-section');
  const grid = document.getElementById('wishlist-grid');
  section.classList.toggle('hidden', list.length === 0);
  grid.innerHTML = '';
  const rates = getRates();
  list.forEach(p => {
    const est = rateForMetal(p.metal) * p.weightGrams;
    const el = document.createElement('div');
    el.className = 'card';
    el.innerHTML = `
      <div class="card-media">
        <img src="${p.imageUrl}" alt="${p.name}">
      </div>
      <div class="card-content">
        <div class="title-row">
          <div class="title">${p.name}</div>
          <div class="meta">${formatCurrency(est, rates.currency)}</div>
        </div>
      </div>
      <div class="actions-row">
        <button class="btn sm" data-action="enquire">Enquire</button>
        <button class="btn sm" data-action="remove">Remove</button>
      </div>
    `;
    el.querySelector('[data-action="enquire"]').addEventListener('click', () => openEnquiry(p));
    el.querySelector('[data-action="remove"]').addEventListener('click', () => {
      removeFromWishlist(p.id);
      renderWishlist();
    });
    grid.appendChild(el);
  });
}

export function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 1600);
}

function buildWhatsAppLink(contact, product, name, phone, message) {
  const text = `Enquiry for ${product.name} (${product.metal}, ${product.category}, ${product.weightGrams}g). Caller: ${name}, ${phone}. ${message || ''}`;
  const u = `https://wa.me/${contact.whatsapp}?text=${encodeURIComponent(text)}`;
  return u;
}

function getContact() {
  try {
    const raw = localStorage.getItem('usg_contact');
    const c = raw ? JSON.parse(raw) : null;
    return c || { phone: '', whatsapp: '' };
  } catch {
    return { phone: '', whatsapp: '' };
  }
}

export function renderFooterContact() {
  const c = getContact();
  document.getElementById('contact-phone').textContent = c.phone || '—';
  document.getElementById('contact-whatsapp').textContent = c.whatsapp || '—';
}

export function openEnquiry(product) {
  const m = document.getElementById('enquiry-modal');
  const call = document.getElementById('enquiry-call');
  const wa = document.getElementById('enquiry-whatsapp');
  const c = getContact();
  call.href = c.phone ? `tel:${c.phone}` : '#';
  wa.href = c.whatsapp ? buildWhatsAppLink(c, product, '', '', '') : '#';
  m.dataset.productId = product.id;
  m.classList.remove('hidden');
}

export function closeEnquiry() {
  const m = document.getElementById('enquiry-modal');
  m.classList.add('hidden');
}

export function initEnquiryForm() {
  const form = document.getElementById('enquiry-form');
  form.addEventListener('submit', e => {
    e.preventDefault();
    const name = document.getElementById('enq-name').value.trim();
    const phone = document.getElementById('enq-phone').value.trim();
    const msg = document.getElementById('enq-message').value.trim();
    const pid = document.getElementById('enquiry-modal').dataset.productId;
    const c = getContact();
    const products = JSON.parse(localStorage.getItem('usg_products') || '[]');
    const product = products.find(x => x.id === pid);
    if (!product || !c.whatsapp) {
      showToast('Contact not set or product missing');
      return;
    }
    const link = buildWhatsAppLink(c, product, name, phone, msg);
    window.open(link, '_blank');
    closeEnquiry();
    showToast('Opening WhatsApp');
  });
}
