function openStockModal(id, product, branch, stock, returnTo) {
  document.getElementById('modalInventoryId').value = id;
  document.getElementById('modalProduct').textContent = product;
  document.getElementById('modalBranch').textContent = branch;
  document.getElementById('modalStock').value = stock;
  const returnField = document.getElementById('modalReturnTo');
  if (returnField && returnTo) returnField.value = returnTo;
  document.getElementById('stockModal').classList.add('open');
  document.getElementById('modalStock').focus();
}
function hideStockModal() {
  const modal = document.getElementById('stockModal');
  if (modal) modal.classList.remove('open');
}
function closeStockModal(event) {
  if (event.target.id === 'stockModal') hideStockModal();
}
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') hideStockModal();
});
