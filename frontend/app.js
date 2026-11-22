const API_BASE = (window.FARMACERCA_CONFIG?.API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
const page = document.body.dataset.page;

const navItems = [
  ["dashboard", "index.html", "⌂", "Dashboard"],
  ["inventory", "inventory.html", "▦", "Inventario"],
  ["branches", "branches.html", "⌖", "Sucursales"],
  ["transfers", "transfers.html", "⇄", "Transferencias"],
  ["alerts", "alerts.html", "!", "Alertas"],
];

function esc(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatDate(value) {
  if (!value) return "—";
  const d = new Date(`${value}T00:00:00`);
  return new Intl.DateTimeFormat("es-PE", { day: "2-digit", month: "2-digit", year: "numeric" }).format(d);
}

function formatDateTime(value) {
  if (!value) return "";
  const d = new Date(value);
  return new Intl.DateTimeFormat("es-PE", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }).format(d);
}

function money(value) {
  return new Intl.NumberFormat("es-PE", { style: "currency", currency: "PEN" }).format(Number(value || 0));
}

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  let body = null;
  try { body = await response.json(); } catch (_) {}
  if (!response.ok) throw new Error(body?.detail || `Error ${response.status}`);
  return body;
}

function shell(content) {
  const active = page === "product" ? "inventory" : page;
  const nav = navItems.map(([key, href, icon, label]) => `
    <a class="nav-item ${active === key ? "active" : ""}" href="${href}">
      <b>${icon}</b><span>${label}</span>
    </a>`).join("");

  document.getElementById("app").innerHTML = `
    <div class="app-shell">
      <aside class="sidebar" id="sidebar">
        <a class="brand" href="index.html">
          <div class="brand-mark"><span>F</span><i>+</i></div>
          <div><strong>FarmaCerca</strong><span>Gestión de inventario</span></div>
        </a>
        <nav>${nav}</nav>
      </aside>
      <main>
        <header class="topbar">
          <button class="menu-button" id="menuButton" aria-label="Abrir menú">☰</button>
          <div class="topbar-title"><span>Operaciones</span><strong>Inventario centralizado</strong></div>
          <div class="user-chip"><strong>Administrador</strong><small>Gestión de inventario</small></div>
        </header>
        <section class="content" id="content">${content}</section>
      </main>
    </div>
    <div id="toastRoot"></div>
    <div id="modalRoot"></div>`;

  document.getElementById("menuButton")?.addEventListener("click", () => document.body.classList.toggle("menu-open"));
}

function loading() {
  shell(`<div class="page-state"><div class="spinner"></div><strong>Cargando información…</strong></div>`);
}

function fail(error) {
  shell(`<div class="page-state error-state"><strong>No se pudo cargar la información</strong><p>${esc(error.message)}</p><button class="primary-button" onclick="location.reload()">Reintentar</button></div>`);
}

function toast(message, type = "success") {
  const root = document.getElementById("toastRoot");
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = message;
  root.appendChild(el);
  setTimeout(() => el.remove(), 3200);
}

function statusPill(status) {
  const map = { available: ["Disponible", "available"], low: ["Stock bajo", "low"], out: ["Agotado", "out"], expiry: ["Por vencer", "expiry"] };
  const [label, cls] = map[status] || [status, ""];
  return `<span class="status-pill ${cls}">${label}</span>`;
}

function pageHeading(eyebrow, title, subtitle, action = "") {
  return `<div class="page-heading"><div><span class="eyebrow">${eyebrow}</span><h1>${title}</h1><p>${subtitle}</p></div>${action}</div>`;
}

async function renderDashboard() {
  const data = await api("/api/dashboard");
  const s = data.stats;
  const alerts = data.alerts.map(a => `
    <div class="alert-item">
      <span class="status-dot ${a.alert_type === "Agotado" ? "danger" : a.alert_type === "Stock bajo" ? "warning" : "purple"}"></span>
      <div class="grow"><strong>${esc(a.product)}</strong><span>${esc(a.district)} · ${esc(a.sku)}</span></div>
      <div class="align-right"><strong>${a.stock} u.</strong><span>${esc(a.alert_type)}</span></div>
    </div>`).join("") || `<div class="empty-state">Sin alertas activas.</div>`;

  const branches = data.branch_summary.map(b => `
    <div class="branch-row">
      <div class="branch-label"><strong>${esc(b.district)}</strong><span>${b.low_stock} bajo stock · ${b.unavailable} agotados</span></div>
      <div class="bar"><span style="width:${b.health}%"></span></div><strong>${b.health}%</strong>
    </div>`).join("");

  const recent = data.recent.map(m => `
    <div class="movement"><span class="movement-icon">${m.quantity < 0 ? "−" : "+"}</span><div class="grow"><strong>${esc(m.product)}</strong><span>${esc(m.district)} · ${esc(m.movement_type.replaceAll("_", " "))}</span></div><strong class="${m.quantity < 0 ? "negative" : "positive"}">${m.quantity > 0 ? "+" : ""}${m.quantity}</strong></div>
  `).join("") || `<div class="empty-state">Los movimientos aparecerán aquí.</div>`;

  shell(`
    ${pageHeading("Resumen operativo", "Dashboard de inventario", "Monitorea disponibilidad, alertas y movimientos en todas las sucursales.", `<a class="primary-button" href="inventory.html">Buscar producto →</a>`)}
    <div class="stats-grid stats-grid-6">
      <article class="stat-card"><span class="stat-icon">⌂</span><div><small>Sucursales</small><strong>${s.branches}</strong><span>integradas al sistema</span></div></article>
      <article class="stat-card magenta"><span class="stat-icon">▦</span><div><small>Productos</small><strong>${s.products}</strong><span>en catálogo activo</span></div></article>
      <article class="stat-card healthy"><span class="stat-icon">✓</span><div><small>Cobertura saludable</small><strong>${s.coverage}%</strong><span>sobre stock mínimo</span></div></article>
      <article class="stat-card warning"><span class="stat-icon">!</span><div><small>Stock bajo</small><strong>${s.low_stock}</strong><span>requieren atención</span></div></article>
      <article class="stat-card danger"><span class="stat-icon">×</span><div><small>Agotados</small><strong>${s.out_of_stock}</strong><span>riesgo de venta perdida</span></div></article>
      <article class="stat-card purple"><span class="stat-icon">◷</span><div><small>Por vencer</small><strong>${s.expiring}</strong><span>en próximos 60 días</span></div></article>
    </div>
    <div class="grid-2">
      <section class="panel"><div class="panel-heading"><div><span class="eyebrow">Atención requerida</span><h2>Alertas recientes</h2></div><a href="alerts.html">Ver todas</a></div><div class="alert-list">${alerts}</div></section>
      <section class="panel"><div class="panel-heading"><div><span class="eyebrow">Red de locales</span><h2>Salud del inventario</h2></div><a href="branches.html">Ver sucursales</a></div><div class="branch-list">${branches}</div></section>
    </div>
    <section class="panel dashboard-bottom"><div class="panel-heading"><div><span class="eyebrow">Trazabilidad</span><h2>Últimos movimientos</h2></div><a href="transfers.html">Ver transferencias</a></div><div class="movement-list">${recent}</div></section>
  `);
}

async function renderInventory() {
  const params = new URLSearchParams(location.search);
  const q = params.get("q") || "";
  const branch = params.get("branch") || "";
  const status = params.get("status") || "all";
  const data = await api(`/api/inventory?${new URLSearchParams({ q, branch, status }).toString()}`);
  const branchOptions = data.branches.map(b => `<option value="${b.id}" ${String(b.id) === branch ? "selected" : ""}>${esc(b.district)}</option>`).join("");
  const rows = data.rows.map(r => `
    <tr>
      <td><a class="product-link" href="product.html?id=${r.product_id}"><div class="product-cell"><div class="product-avatar">Rx</div><div><strong>${esc(r.name)}</strong><span>${esc(r.sku)} · ${esc(r.category)}</span></div></div></a></td>
      <td><strong>${esc(r.district)}</strong></td><td class="stock-number">${r.stock}</td><td>${statusPill(r.status)}</td><td>${formatDate(r.expiry_date)}</td>
      <td><div class="action-group"><a class="ghost-button" href="product.html?id=${r.product_id}">Ver</a><button class="ghost-button edit-stock" data-id="${r.inventory_id}" data-name="${esc(r.name)}" data-branch="${esc(r.district)}" data-stock="${r.stock}">Editar</button></div></td>
    </tr>`).join("") || `<tr><td colspan="6" class="empty-state">No se encontraron resultados.</td></tr>`;

  shell(`
    ${pageHeading("Consulta centralizada", "Inventario por sucursal", "Busca productos y revisa su disponibilidad en toda la red.")}
    <form class="filter-panel" id="filterForm">
      <label class="search-field"><span>⌕</span><input type="search" name="q" value="${esc(q)}" placeholder="Buscar medicamento, SKU o categoría..." /></label>
      <select name="branch"><option value="">Todas las sucursales</option>${branchOptions}</select>
      <select name="status"><option value="all" ${status === "all" ? "selected" : ""}>Todos los estados</option><option value="available" ${status === "available" ? "selected" : ""}>Disponible</option><option value="low" ${status === "low" ? "selected" : ""}>Stock bajo</option><option value="out" ${status === "out" ? "selected" : ""}>Agotado</option></select>
      <button class="primary-button" type="submit">Filtrar</button>
    </form>
    <section class="panel table-panel"><div class="panel-heading"><div><span class="eyebrow">Resultados</span><h2>${data.rows.length} registros encontrados</h2></div></div><div class="table-wrap"><table><thead><tr><th>Producto</th><th>Sucursal</th><th>Stock</th><th>Estado</th><th>Vencimiento</th><th>Acciones</th></tr></thead><tbody>${rows}</tbody></table></div></section>
  `);

  document.getElementById("filterForm").addEventListener("submit", e => {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const p = new URLSearchParams();
    for (const [k, v] of form.entries()) if (v) p.set(k, v);
    location.href = `inventory.html?${p.toString()}`;
  });
  document.querySelectorAll(".edit-stock").forEach(btn => btn.addEventListener("click", () => openStockModal(btn.dataset)));
}

function openStockModal(data) {
  document.getElementById("modalRoot").innerHTML = `
    <div class="modal-backdrop open" id="stockModal">
      <div class="modal"><button class="modal-close" id="closeModal">×</button><span class="eyebrow">Actualizar inventario</span><h2>${esc(data.name)}</h2><p>${esc(data.branch)}</p>
        <form id="stockForm"><label>Nuevo stock<input type="number" min="0" name="stock" value="${Number(data.stock)}" required /></label><button class="primary-button full">Guardar cambio</button></form>
      </div>
    </div>`;
  const close = () => document.getElementById("modalRoot").innerHTML = "";
  document.getElementById("closeModal").addEventListener("click", close);
  document.getElementById("stockModal").addEventListener("click", e => { if (e.target.id === "stockModal") close(); });
  document.getElementById("stockForm").addEventListener("submit", async e => {
    e.preventDefault();
    try {
      await api(`/api/inventory/${data.id}`, { method: "PATCH", body: JSON.stringify({ stock: Number(new FormData(e.currentTarget).get("stock")) }) });
      close(); toast("Stock actualizado correctamente"); setTimeout(() => location.reload(), 450);
    } catch (err) { toast(err.message, "error"); }
  });
}

async function renderBranches() {
  const data = await api("/api/branches");
  const cards = data.branches.map(b => `
    <article class="branch-card"><div class="branch-card-head"><span class="branch-pin">⌖</span><div class="grow"><small>Sucursal</small><h2>${esc(b.district)}</h2><span>${esc(b.name)}</span></div><span class="health-badge ${b.health >= 70 ? "good" : b.health >= 50 ? "medium" : "risk"}">${b.health}% salud</span></div>
      <div class="health-progress"><span style="width:${b.health}%"></span></div>
      <div class="branch-metrics"><div><small>Unidades</small><strong>${b.units}</strong></div><div><small>Productos</small><strong>${b.products}</strong></div><div class="metric-warning"><small>Stock bajo</small><strong>${b.low}</strong></div><div class="metric-danger"><small>Agotados</small><strong>${b.out}</strong></div></div>
      <div class="branch-card-actions"><a class="primary-button" href="inventory.html?branch=${b.id}">Ver inventario</a></div></article>`).join("");
  shell(`${pageHeading("Red de locales", "Sucursales", "Compara la situación del inventario entre sedes.")}<div class="branch-cards">${cards}</div>`);
}

async function renderAlerts() {
  const data = await api("/api/alerts");
  const rows = data.alerts.map(a => `
    <tr><td>${statusPill(a.status)}</td><td><a class="text-link" href="product.html?id=${a.product_id}"><strong>${esc(a.name)}</strong></a><span class="subtext">${esc(a.sku)}</span></td><td>${esc(a.district)}</td><td class="stock-number">${a.stock}</td><td>${a.min_stock}</td><td>${formatDate(a.expiry_date)}</td><td><div class="action-group"><a class="ghost-button" href="product.html?id=${a.product_id}">Ver</a><a class="primary-button tiny" href="transfers.html?product_id=${a.product_id}&destination_branch_id=${a.branch_id}">Transferir</a></div></td></tr>`).join("") || `<tr><td colspan="7" class="empty-state">No hay alertas activas.</td></tr>`;
  shell(`${pageHeading("Control preventivo", "Alertas de inventario", "Prioriza agotados, niveles bajos y productos próximos a vencer.")}<div class="legend"><span><i class="dot red"></i>Agotado</span><span><i class="dot amber"></i>Stock bajo</span><span><i class="dot violet"></i>Próximo a vencer</span></div><section class="panel table-panel"><div class="table-wrap"><table><thead><tr><th>Prioridad</th><th>Producto</th><th>Sucursal</th><th>Stock</th><th>Mínimo</th><th>Vencimiento</th><th>Acciones</th></tr></thead><tbody>${rows}</tbody></table></div></section>`);
}

async function renderTransfers() {
  const params = new URLSearchParams(location.search);
  const data = await api("/api/transfers");
  const productId = params.get("product_id") || "";
  const sourceId = params.get("source_branch_id") || "";
  const destId = params.get("destination_branch_id") || "";
  const quantity = params.get("quantity") || "";
  const pOpts = data.products.map(p => `<option value="${p.id}" ${String(p.id) === productId ? "selected" : ""}>${esc(p.name)} · ${esc(p.sku)}</option>`).join("");
  const branchOpts = selected => data.branches.map(b => `<option value="${b.id}" ${String(b.id) === selected ? "selected" : ""}>${esc(b.district)}</option>`).join("");
  const recent = data.recent.map(m => `<div class="movement"><span class="movement-icon">${m.movement_type === "TRANSFERENCIA_SALIDA" ? "→" : "←"}</span><div class="grow"><strong>${esc(m.product)}</strong><span>${esc(m.district)} · ${formatDateTime(m.created_at)}</span></div><strong class="${m.quantity < 0 ? "negative" : "positive"}">${m.quantity > 0 ? "+" : ""}${m.quantity}</strong></div>`).join("") || `<div class="empty-state">Todavía no se han realizado transferencias.</div>`;

  shell(`${pageHeading("Redistribución de stock", "Transferencias entre sucursales", "Mueve unidades desde una sede con disponibilidad hacia otra que las necesita.")}<div class="grid-2 transfer-layout"><section class="panel form-panel"><div class="panel-heading"><div><span class="eyebrow">Nueva operación</span><h2>Registrar transferencia</h2></div></div><form id="transferForm" class="stack-form"><label>Producto<select name="product_id" required><option value="">Seleccionar producto</option>${pOpts}</select></label><div class="form-grid"><label>Desde<select name="source_branch_id" required><option value="">Sucursal origen</option>${branchOpts(sourceId)}</select></label><label>Hacia<select name="destination_branch_id" required><option value="">Sucursal destino</option>${branchOpts(destId)}</select></label></div><label>Cantidad de unidades<input type="number" min="1" name="quantity" value="${esc(quantity)}" required placeholder="Ej. 15" /></label><div class="info-box">El sistema valida el stock disponible y actualiza automáticamente origen, destino y trazabilidad.</div><button class="primary-button full">Confirmar transferencia</button></form></section><section class="panel"><div class="panel-heading"><div><span class="eyebrow">Trazabilidad</span><h2>Movimientos recientes</h2></div></div><div class="movement-list">${recent}</div></section></div>`);

  document.getElementById("transferForm").addEventListener("submit", async e => {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    const payload = Object.fromEntries([...f.entries()].map(([k,v]) => [k, Number(v)]));
    try {
      await api("/api/transfers", { method: "POST", body: JSON.stringify(payload) });
      toast("Transferencia registrada correctamente"); setTimeout(() => location.href = "transfers.html", 550);
    } catch (err) { toast(err.message, "error"); }
  });
}

async function renderProduct() {
  const id = new URLSearchParams(location.search).get("id");
  if (!id) throw new Error("No se indicó un producto");
  const data = await api(`/api/products/${id}`);
  const p = data.product;
  const rec = data.recommendation;
  const recommendation = rec.source && rec.destination && rec.quantity > 0 ? `<section class="smart-recommendation"><div class="recommendation-icon">↔</div><div class="grow"><span class="eyebrow">Recomendación automática</span><h2>Redistribuir ${rec.quantity} unidades</h2><p><strong>${esc(rec.source.district)}</strong> tiene ${rec.source.stock} u. y <strong>${esc(rec.destination.district)}</strong> tiene ${rec.destination.stock} u.</p></div><a class="primary-button" href="transfers.html?product_id=${p.id}&source_branch_id=${rec.source.branch_id}&destination_branch_id=${rec.destination.branch_id}&quantity=${rec.quantity}">Crear transferencia →</a></section>` : "";
  const invRows = data.inventory.map(r => `<tr><td><strong>${esc(r.district)}</strong></td><td class="stock-number">${r.stock}</td><td>${statusPill(r.status)}${r.expiring ? ` ${statusPill("expiry")}` : ""}</td><td>${formatDate(r.expiry_date)}</td><td><div class="action-group"><a class="ghost-button" href="transfers.html?product_id=${p.id}&destination_branch_id=${r.branch_id}">Transferir</a><button class="ghost-button edit-stock" data-id="${r.inventory_id}" data-name="${esc(p.name)}" data-branch="${esc(r.district)}" data-stock="${r.stock}">Editar</button></div></td></tr>`).join("");
  const recent = data.recent.map(m => `<div class="movement"><span class="movement-icon">${m.quantity < 0 ? "−" : "+"}</span><div class="grow"><strong>${esc(m.district)}</strong><span>${esc(m.movement_type.replaceAll("_", " "))}${m.note ? ` · ${esc(m.note)}` : ""}</span></div><strong class="${m.quantity < 0 ? "negative" : "positive"}">${m.quantity > 0 ? "+" : ""}${m.quantity}</strong></div>`).join("") || `<div class="empty-state">Todavía no hay movimientos registrados.</div>`;

  shell(`<div class="breadcrumb"><a href="inventory.html">Inventario</a><span>›</span><span>${esc(p.name)}</span></div>${pageHeading("Detalle de producto", esc(p.name), `${esc(p.sku)} · ${esc(p.category)} · ${money(p.price)}`, `<a class="primary-button" href="transfers.html?product_id=${p.id}">Nueva transferencia →</a>`)}<div class="stats-grid product-stats"><article class="stat-card"><span class="stat-icon">Σ</span><div><small>Stock total</small><strong>${data.metrics.total_stock}</strong><span>unidades en todas las sedes</span></div></article><article class="stat-card healthy"><span class="stat-icon">✓</span><div><small>Sedes saludables</small><strong>${data.metrics.available_branches}</strong><span>por encima del mínimo</span></div></article><article class="stat-card warning"><span class="stat-icon">!</span><div><small>Sedes críticas</small><strong>${data.metrics.critical_branches}</strong><span>stock bajo o agotado</span></div></article><article class="stat-card"><span class="stat-icon">↓</span><div><small>Stock mínimo</small><strong>${p.min_stock}</strong><span>umbral configurado</span></div></article></div>${recommendation}<div class="grid-2 product-layout"><section class="panel table-panel"><div class="panel-heading"><div><span class="eyebrow">Disponibilidad</span><h2>Stock por sucursal</h2></div></div><div class="table-wrap"><table class="detail-table"><thead><tr><th>Sucursal</th><th>Stock</th><th>Estado</th><th>Vencimiento</th><th>Acción</th></tr></thead><tbody>${invRows}</tbody></table></div></section><section class="panel"><div class="panel-heading"><div><span class="eyebrow">Trazabilidad</span><h2>Movimientos recientes</h2></div></div><div class="movement-list">${recent}</div></section></div>`);
  document.querySelectorAll(".edit-stock").forEach(btn => btn.addEventListener("click", () => openStockModal(btn.dataset)));
}

async function boot() {
  loading();
  try {
    if (page === "dashboard") await renderDashboard();
    else if (page === "inventory") await renderInventory();
    else if (page === "branches") await renderBranches();
    else if (page === "alerts") await renderAlerts();
    else if (page === "transfers") await renderTransfers();
    else if (page === "product") await renderProduct();
    else throw new Error("Página no reconocida");
  } catch (err) { console.error(err); fail(err); }
}

boot();
