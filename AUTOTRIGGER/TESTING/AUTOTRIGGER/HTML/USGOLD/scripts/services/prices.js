const LS_KEY = 'usg_prices';
const defaultRates = { gold: 7200, silver: 90, currency: 'INR', lastUpdated: null };

export function getRates() {
  const raw = localStorage.getItem(LS_KEY);
  if (!raw) return { ...defaultRates };
  try { return JSON.parse(raw); } catch { return { ...defaultRates }; }
}

export function setRates(rates) {
  const merged = { ...getRates(), ...rates };
  localStorage.setItem(LS_KEY, JSON.stringify(merged));
  return merged;
}

export async function fetchLiveRates() {
  try {
    // Use a CORS proxy to ensure browser access works
    const target = 'https://data-asg.goldprice.org/dbXRates/INR';
    const res = await fetch(`https://api.allorigins.win/raw?url=${encodeURIComponent(target)}`);
    if (!res.ok) throw new Error('API failed');
    const data = await res.json();
    if (data.items && data.items[0]) {
      const item = data.items[0];
      // API returns price per Ounce (31.1035g)
      const goldOz = item.xauPrice;
      const silverOz = item.xagPrice;
      
      const gold24k = goldOz / 31.1035;
      const silver = silverOz / 31.1035;
      
      // We use 22K for jewellery pricing (approx 91.6% of 24K)
      // But for "Today's Rate" display we might want 24K.
      // However, product price estimation usually uses 22K.
      // Let's store 22K as 'gold' for calculations, and add 'gold24k' for display if needed.
      // For simplicity and safety, let's use 22K for the 'gold' key which drives product prices.
      
      const gold22k = gold24k * 0.916;

      const newRates = {
        gold: Math.round(gold22k), // Round to nearest rupee
        silver: Math.round(silver),
        gold24k: Math.round(gold24k),
        lastUpdated: new Date().toISOString()
      };
      return setRates(newRates);
    }
  } catch (e) {
    console.error('Failed to fetch live rates', e);
    return getRates();
  }
}

export function formatCurrency(amount, currency = 'INR') {
  try {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency }).format(amount);
  } catch {
    return `₹${amount.toLocaleString('en-IN')}`;
  }
}

export function rateForMetal(metal) {
  const r = getRates();
  return metal === 'gold' ? r.gold : r.silver;
}
