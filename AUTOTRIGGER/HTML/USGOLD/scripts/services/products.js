const LS_KEY = 'usg_products';

async function loadFromJson() {
  const res = await fetch('data/products.json');
  const data = await res.json();
  return data;
}

export async function getProducts() {
  const raw = localStorage.getItem(LS_KEY);
  if (raw) {
    try { return JSON.parse(raw); } catch {}
  }
  const data = await loadFromJson();
  localStorage.setItem(LS_KEY, JSON.stringify(data));
  return data;
}

export function setProducts(products) {
  localStorage.setItem(LS_KEY, JSON.stringify(products));
  return products;
}

export function addProduct(p) {
  return getProducts().then(list => {
    const next = [...list, p];
    setProducts(next);
    return p;
  });
}

export function deleteProduct(id) {
  return getProducts().then(list => {
    const next = list.filter(x => x.id !== id);
    setProducts(next);
    return next;
  });
}

export function updateProduct(id, patch) {
  return getProducts().then(list => {
    const next = list.map(x => x.id === id ? { ...x, ...patch } : x);
    setProducts(next);
    return next.find(x => x.id === id);
  });
}

export function filterProducts(list, f) {
  return list.filter(p => {
    const byMetal = f.metal === 'all' || p.metal === f.metal;
    const byCategory = f.category === 'all' || p.category === f.category;
    const byGender = f.gender === 'all' || p.gender === f.gender;
    const byWeight = p.weightGrams <= f.weightMax;
    const byPrice = !f.estimatePrice || f.estimatePrice(p) <= f.priceMax;
    return byMetal && byCategory && byGender && byWeight && byPrice;
  });
}
