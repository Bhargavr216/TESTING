const state = { items: [] };

export function addToWishlist(product) {
  if (!state.items.find(x => x.id === product.id)) state.items.push(product);
  return [...state.items];
}

export function removeFromWishlist(id) {
  const idx = state.items.findIndex(x => x.id === id);
  if (idx >= 0) state.items.splice(idx, 1);
  return [...state.items];
}

export function getWishlist() {
  return [...state.items];
}

export function clearWishlistOnReload() {
  state.items.length = 0;
}
