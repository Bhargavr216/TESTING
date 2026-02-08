document.addEventListener('DOMContentLoaded', () => {
  const qtyInputs = document.querySelectorAll('input.qty');
  qtyInputs.forEach(i => {
    i.addEventListener('input', () => {
      const v = parseInt(i.value, 10);
      if (isNaN(v) || v < 1) i.value = 1;
    });
  });
});