import { getProducts, filterProducts } from './services/products.js';
import { getRates, fetchLiveRates } from './services/prices.js';
import { renderRates, renderProducts, renderWishlist, showToast, openEnquiry, closeEnquiry, initEnquiryForm, renderFooterContact } from './ui.js';
import { clearWishlistOnReload } from './wishlist.js';
import { openTryMe, closeTryMe, initTryMeControls } from './tryme.js';

let allProducts = [];

function renderHomeText() {
  try {
    const h = JSON.parse(localStorage.getItem('usg_home') || '{}');
    if (h.heroTitle) document.querySelector('.hero-title').textContent = h.heroTitle;
    if (h.heroSubtitle) document.querySelector('.hero-subtitle').textContent = h.heroSubtitle;
  } catch {}
}

function initNav() {
  document.querySelectorAll('.nav a[data-nav]').forEach(a => {
    a.addEventListener('click', e => {
      e.preventDefault();
      const t = a.dataset.nav;
      document.querySelectorAll('.nav a').forEach(x => x.classList.remove('active'));
      a.classList.add('active');
      if (t === 'home') {
        document.querySelector('.filters').classList.remove('hidden');
        document.querySelector('.products').classList.remove('hidden');
        document.getElementById('wishlist-section').classList.add('hidden');
      } else if (t === 'wishlist') {
        document.querySelector('.filters').classList.add('hidden');
        document.querySelector('.products').classList.add('hidden');
        renderWishlist();
        document.getElementById('wishlist-section').classList.remove('hidden');
      } else if (t === 'gold' || t === 'silver') {
        document.querySelector('.filters').classList.remove('hidden');
        document.querySelector('.products').classList.remove('hidden');
        document.getElementById('filter-metal').value = t;
        applyFilters();
      }
    });
  });
}

function initHeroActions() {
  document.querySelectorAll('[data-filter-metal]').forEach(b => {
    b.addEventListener('click', () => {
      document.getElementById('filter-metal').value = b.dataset.filterMetal;
      applyFilters();
    });
  });
}

function initFilters() {
  const fm = document.getElementById('filter-metal');
  const fc = document.getElementById('filter-category');
  const fg = document.getElementById('filter-gender');
  const fw = document.getElementById('filter-weight');
  const fp = document.getElementById('filter-price');
  const reset = document.getElementById('reset-filters');
  fm.addEventListener('change', applyFilters);
  fc.addEventListener('change', applyFilters);
  fg.addEventListener('change', applyFilters);
  fw.addEventListener('input', () => {
    document.getElementById('filter-weight-val').textContent = `≤ ${fw.value}g`;
    applyFilters();
  });
  fp.addEventListener('input', () => {
    const v = Number(fp.value);
    document.getElementById('filter-price-val').textContent = `≤ ₹${v.toLocaleString('en-IN')}`;
    applyFilters();
  });
  reset.addEventListener('click', () => {
    fm.value = 'all';
    fc.value = 'all';
    fg.value = 'all';
    fw.value = 100;
    fp.value = 500000;
    document.getElementById('filter-weight-val').textContent = `≤ 100g`;
    document.getElementById('filter-price-val').textContent = `≤ ₹${(500000).toLocaleString('en-IN')}`;
    applyFilters();
  });
}

function applyFilters() {
  const fm = document.getElementById('filter-metal').value;
  const fc = document.getElementById('filter-category').value;
  const fg = document.getElementById('filter-gender').value;
  const fw = Number(document.getElementById('filter-weight').value);
  const fp = Number(document.getElementById('filter-price').value);
  const rates = getRates();
  const filtered = filterProducts(allProducts, {
    metal: fm,
    category: fc,
    gender: fg,
    weightMax: fw,
    priceMax: fp,
    estimatePrice: p => (p.metal === 'gold' ? rates.gold : rates.silver) * p.weightGrams
  });
  renderProducts(filtered);
}

function initModals() {
  document.querySelectorAll('.modal-close').forEach(b => {
    b.addEventListener('click', () => {
      const t = b.dataset.close;
      if (t === 'enquiry') closeEnquiry();
      if (t === 'tryme') closeTryMe();
    });
  });
}

function initFooter() {
  document.getElementById('year').textContent = new Date().getFullYear();
  renderFooterContact();
}

async function boot() {
  clearWishlistOnReload();
  initNav();
  initHeroActions();
  initFilters();
  initModals();
  initEnquiryForm();
  initTryMeControls();
  initFooter();
  renderRates();
  renderHomeText();
  allProducts = await getProducts();
  applyFilters();
  
  // Fetch live rates
  fetchLiveRates().then(updated => {
    if (updated.lastUpdated) {
      renderRates();
      applyFilters(); // Re-calculate product prices
      showToast('Live gold rates updated');
    }
  });

  showToast('Welcome to USGolds');
}

boot();
