// Global state
let config = null;
let currentService = null;
let tableData = []; // Store table data for multiple mode

// Initialize app
document.addEventListener('DOMContentLoaded', async () => {
    await loadConfiguration();
    setupEventListeners();
});

function uuidV4() {
    if (window.crypto && typeof window.crypto.randomUUID === 'function') {
        return window.crypto.randomUUID();
    }

    const bytes = new Uint8Array(16);
    if (window.crypto && typeof window.crypto.getRandomValues === 'function') {
        window.crypto.getRandomValues(bytes);
    } else {
        for (let i = 0; i < bytes.length; i++) bytes[i] = Math.floor(Math.random() * 256);
    }

    // RFC 4122 version 4
    bytes[6] = (bytes[6] & 0x0f) | 0x40;
    bytes[8] = (bytes[8] & 0x3f) | 0x80;

    const hex = Array.from(bytes, b => b.toString(16).padStart(2, '0'));
    return `${hex.slice(0, 4).join('')}-${hex.slice(4, 6).join('')}-${hex.slice(6, 8).join('')}-${hex.slice(8, 10).join('')}-${hex.slice(10, 16).join('')}`;
}

function toFieldId(fieldKey) {
    return `field_${String(fieldKey).replace(/[^\w-]/g, '_')}`;
}

function normalizeFieldType(type) {
    const t = String(type || 'TEXT').trim().toUpperCase();
    if (t === 'TEXT') return 'text';
    if (t === 'NUMBER') return 'number';
    if (t === 'EMAIL') return 'email';
    if (t === 'URL') return 'url';
    if (t === 'TEXTAREA') return 'textarea';
    if (t === 'SELECT') return 'select';
    if (t === 'UUID') return 'uuid';
    return t.toLowerCase();
}

function normalizeEditableFields(service) {
    const editableFields = Array.isArray(service.editableFields) ? service.editableFields : [];

    // Backwards-compatible support: editableFields: ["field1", "field2"] with fieldLabels/fieldTypes/fieldOptions
    if (editableFields.length > 0 && typeof editableFields[0] === 'string') {
        return editableFields.map((key) => {
            const fieldType = service.fieldTypes?.[key] || 'text';
            const label = service.fieldLabels?.[key] || key;
            const options = service.fieldOptions?.[key] || [];
            return {
                key,
                type: normalizeFieldType(fieldType),
                label,
                placeholder: `Enter ${label}...`,
                options,
                randomValue: false,
                required: true
            };
        });
    }

    // New schema support:
    // editableFields: [{ key, type, label, placeholder, options?, randomValue? }]
    return editableFields
        .map((field) => {
            const key = field?.key ?? field?.path ?? field?.name;
            const label = field?.label || key;
            return {
                key,
                type: normalizeFieldType(field?.type),
                label,
                placeholder: field?.placeholder || `Enter ${label}...`,
                options: field?.options || [],
                // accept common typos from config
                randomValue: Boolean(field?.randomValue || field?.radomValue || field?.ramdonValue),
                required: field?.required === undefined ? true : Boolean(field.required)
            };
        })
        .filter(f => typeof f.key === 'string' && f.key.trim() !== '');
}

function isUnsafePathSegment(segment) {
    return segment === '__proto__' || segment === 'prototype' || segment === 'constructor';
}

function deepSet(target, dottedPath, value) {
    if (typeof dottedPath !== 'string' || dottedPath.trim() === '') return;

    const segments = dottedPath.split('.').map(s => s.trim()).filter(Boolean);
    if (segments.length === 0) return;
    if (segments.some(isUnsafePathSegment)) {
        throw new Error(`Unsafe field path: ${dottedPath}`);
    }

    let cursor = target;
    for (let i = 0; i < segments.length - 1; i++) {
        const segment = segments[i];
        if (cursor[segment] === undefined || cursor[segment] === null || typeof cursor[segment] !== 'object') {
            cursor[segment] = {};
        }
        cursor = cursor[segment];
    }

    cursor[segments[segments.length - 1]] = value;
}

function applyOverrides(payloadTemplate, overrides) {
    if (!overrides || typeof overrides !== 'object') return payloadTemplate;

    for (const [key, value] of Object.entries(overrides)) {
        if (key.includes('.')) {
            deepSet(payloadTemplate, key, value);
        } else {
            payloadTemplate[key] = value;
        }
    }

    return payloadTemplate;
}

function getTemplateForService(service) {
    return service.eventPayload || service.payload || {};
}

function getRequiredFieldKeys(service) {
    return normalizeEditableFields(service)
        .filter(f => f.required)
        .map(f => f.key);
}

function findMissingRequiredKeys(requiredKeys, payloadLike) {
    const missing = [];
    requiredKeys.forEach((key) => {
        const value = payloadLike?.[key];
        if (value === undefined || value === null || value === '') missing.push(key);
    });
    return missing;
}

// Load configuration from server
async function loadConfiguration() {
    try {
        const response = await fetch('/api/config');
        config = await response.json();
        renderServicesList();
    } catch (error) {
        console.error('Error loading configuration:', error);
        showAlert('Failed to load configuration', 'danger');
    }
}

// Setup event listeners
function setupEventListeners() {
    document.querySelectorAll('input[name="triggerMode"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            switchMode(e.target.value);
        });
    });

    const prefixEl = document.getElementById('randomPrefixInput');
    if (prefixEl) {
        prefixEl.addEventListener('input', () => {
            const table = document.getElementById('multiplePayloadTable');
            if (!table) return;
            const toggles = Array.from(document.querySelectorAll('input[id^="multi_random_"]'));
            toggles
                .filter(t => t.checked && t.dataset.fieldKey)
                .forEach(t => applyRandomToMultipleColumn(t.dataset.fieldKey, true));
        });
    }
}

// Render services list on left sidebar
function renderServicesList() {
    const servicesList = document.getElementById('servicesList');
    servicesList.innerHTML = '';

    config.services.forEach((service) => {
        const item = document.createElement('a');
        item.href = '#';
        item.className = 'list-group-item list-group-item-action';
        item.dataset.serviceId = service.id;
        item.innerHTML = `
            <i class="bi bi-gear"></i>
            <span>${service.name}</span>
        `;
        item.addEventListener('click', (e) => {
            e.preventDefault();
            selectService(service.id);
        });
        servicesList.appendChild(item);
    });
}

// Select a service
function selectService(serviceId) {
    // Update active state
    document.querySelectorAll('.list-group-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-service-id="${serviceId}"]`).classList.add('active');

    // Find service config
    currentService = config.services.find(s => s.id === serviceId);

    // Show detail section
    document.getElementById('welcomeSection').style.display = 'none';
    document.getElementById('detailSection').style.display = 'block';

    // Populate service info
    document.getElementById('serviceName').textContent = currentService.name;
    document.getElementById('serviceEventHub').textContent =
        currentService.eventHubName ? `Event Hub: ${currentService.eventHubName}` : 'Event Hub: (not set)';

    // Reset form
    resetForm();

    // Generate form fields
    generateFormFields();
}

// Generate dynamic form fields based on service config
function generateFormFields() {
    const form = document.getElementById('singlePayloadForm');
    form.innerHTML = '';

    const fields = normalizeEditableFields(currentService);

    fields.forEach(field => {
        const fieldKey = field.key;
        const fieldId = toFieldId(fieldKey);

        const formGroup = document.createElement('div');
        formGroup.className = 'form-group';

        const label = document.createElement('label');
        label.htmlFor = fieldId;
        label.className = 'form-label';
        label.textContent = field.label || fieldKey;

        let input;

        if (field.type === 'select') {
            input = document.createElement('select');
            input.className = 'form-select';
            input.id = fieldId;
            input.name = fieldKey;
            input.required = Boolean(field.required);

            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.textContent = `Select ${field.label || fieldKey}...`;
            input.appendChild(defaultOption);

            (field.options || []).forEach(option => {
                const optionElement = document.createElement('option');
                optionElement.value = option;
                optionElement.textContent = option;
                input.appendChild(optionElement);
            });
        } else if (field.type === 'textarea') {
            input = document.createElement('textarea');
            input.className = 'form-control';
            input.id = fieldId;
            input.name = fieldKey;
            input.required = Boolean(field.required);
            input.rows = '4';
            input.placeholder = field.placeholder || `Enter ${field.label || fieldKey}...`;
        } else if (field.type === 'email') {
            input = document.createElement('input');
            input.type = 'email';
            input.className = 'form-control';
            input.id = fieldId;
            input.name = fieldKey;
            input.required = Boolean(field.required);
            input.placeholder = field.placeholder || `Enter ${field.label || fieldKey}...`;
        } else if (field.type === 'url') {
            input = document.createElement('input');
            input.type = 'url';
            input.className = 'form-control';
            input.id = fieldId;
            input.name = fieldKey;
            input.required = Boolean(field.required);
            input.placeholder = field.placeholder || `Enter ${field.label || fieldKey}...`;
        } else if (field.type === 'number') {
            input = document.createElement('input');
            input.type = 'number';
            input.className = 'form-control';
            input.id = fieldId;
            input.name = fieldKey;
            input.required = Boolean(field.required);
            input.placeholder = field.placeholder || `Enter ${field.label || fieldKey}...`;
            input.step = '0.01';
        } else {
            input = document.createElement('input');
            input.type = 'text';
            input.className = 'form-control';
            input.id = fieldId;
            input.name = fieldKey;
            input.required = Boolean(field.required);
            input.placeholder = field.placeholder || `Enter ${field.label || fieldKey}...`;
        }

        formGroup.appendChild(label);
        formGroup.appendChild(input);

        if (field.randomValue) {
            const switchId = `random_${fieldId}`;

            const switchGroup = document.createElement('div');
            switchGroup.className = 'form-check form-switch mt-2';

            const switchInput = document.createElement('input');
            switchInput.className = 'form-check-input';
            switchInput.type = 'checkbox';
            switchInput.role = 'switch';
            switchInput.id = switchId;

            const switchLabel = document.createElement('label');
            switchLabel.className = 'form-check-label';
            switchLabel.htmlFor = switchId;
            switchLabel.textContent = 'Random UUID';

            switchInput.addEventListener('change', () => {
                if (switchInput.checked) {
                    input.value = uuidV4();
                    input.readOnly = true;
                } else {
                    input.readOnly = false;
                    input.value = '';
                    input.focus();
                }
            });

            switchGroup.appendChild(switchInput);
            switchGroup.appendChild(switchLabel);
            formGroup.appendChild(switchGroup);
        }

        form.appendChild(formGroup);
    });
}

// Switch between single and multiple mode
function switchMode(mode) {
    document.getElementById('singleModeForm').style.display = mode === 'single' ? 'block' : 'none';
    document.getElementById('multipleModeForm').style.display = mode === 'multiple' ? 'block' : 'none';
}

function collectSingleFormOverrides() {
    const formData = new FormData(document.getElementById('singlePayloadForm'));
    const overrides = {};

    for (let [key, value] of formData.entries()) {
        if (value) {
            if (!isNaN(value) && value !== '') {
                overrides[key] = parseFloat(value);
            } else if (value === 'true') {
                overrides[key] = true;
            } else if (value === 'false') {
                overrides[key] = false;
            } else {
                overrides[key] = value;
            }
        }
    }

    return overrides;
}

function buildFinalPayloadForSingle(overrides) {
    const template = getTemplateForService(currentService);
    const finalPayload = applyOverrides(JSON.parse(JSON.stringify(template)), overrides);
    finalPayload.timestamp = new Date().toISOString();
    return finalPayload;
}

function buildFinalPayloadsForMultiple(payloads) {
    const template = getTemplateForService(currentService);
    return payloads.map(p => {
        const finalPayload = applyOverrides(JSON.parse(JSON.stringify(template)), p);
        finalPayload.timestamp = new Date().toISOString();
        return finalPayload;
    });
}

function getRandomPrefix() {
    const prefixEl = document.getElementById('randomPrefixInput');
    return prefixEl ? String(prefixEl.value || '') : '';
}

function randomValueForField(field) {
    const prefix = getRandomPrefix();

    if (field.type === 'number') {
        return Math.floor(Math.random() * 1000000);
    }

    if (field.type === 'select') {
        const opts = Array.isArray(field.options) ? field.options : [];
        if (opts.length === 0) return prefix + uuidV4();
        return opts[Math.floor(Math.random() * opts.length)];
    }

    if (field.type === 'email') {
        const safePrefix = prefix.replace(/[^a-zA-Z0-9._-]/g, '');
        return `${safePrefix}${uuidV4().replaceAll('-', '')}@example.com`;
    }

    if (field.type === 'url') {
        const safePrefix = prefix.replace(/[^a-zA-Z0-9._-]/g, '');
        return `https://example.com/${safePrefix}${uuidV4()}`;
    }

    // text/textarea/uuid/default
    return `${prefix}${uuidV4()}`;
}

function applyRandomToMultipleColumn(fieldKey, enabled) {
    const container = document.getElementById('multipleTableContainer');
    if (!container) return;
    const table = document.getElementById('multiplePayloadTable');
    if (!table) return;

    const fields = normalizeEditableFields(currentService || {});
    const field = fields.find(f => f.key === fieldKey) || { key: fieldKey, type: 'text', required: true };

    const all = Array.from(container.querySelectorAll('[data-field-key]'));
    const inputs = all.filter(el => el.dataset.fieldKey === fieldKey);

    inputs.forEach((el) => {
        if (enabled) {
            el.value = String(randomValueForField(field));
            el.readOnly = true;
        } else {
            el.readOnly = false;
            el.value = '';
        }
    });
}

function buildMultipleTable() {
    if (!currentService) {
        showAlert('Please select a service', 'warning');
        return;
    }

    const countEl = document.getElementById('multipleCountInput');
    const container = document.getElementById('multipleTableContainer');
    if (!countEl || !container) return;

    const count = Math.max(1, Math.min(1000, parseInt(countEl.value, 10) || 0));
    countEl.value = String(count);

    const fields = normalizeEditableFields(currentService);
    if (fields.length === 0) {
        showAlert('No editable fields configured for this service', 'warning');
        return;
    }

    container.innerHTML = '';

    const table = document.createElement('table');
    table.className = 'table table-sm table-bordered align-middle';
    table.id = 'multiplePayloadTable';

    const thead = document.createElement('thead');
    const headRow = document.createElement('tr');

    fields.forEach((field) => {
        const th = document.createElement('th');
        th.className = 'text-nowrap';

        const headerWrap = document.createElement('div');
        headerWrap.className = 'd-flex flex-column gap-2';

        const title = document.createElement('div');
        title.className = 'fw-semibold';
        title.textContent = field.label || field.key;

        const randomWrap = document.createElement('div');
        randomWrap.className = 'form-check form-switch m-0';

        const randomId = `multi_random_${toFieldId(field.key)}`;
        const randomInput = document.createElement('input');
        randomInput.className = 'form-check-input';
        randomInput.type = 'checkbox';
        randomInput.role = 'switch';
        randomInput.id = randomId;
        randomInput.dataset.fieldKey = field.key;

        const randomLabel = document.createElement('label');
        randomLabel.className = 'form-check-label small';
        randomLabel.htmlFor = randomId;
        randomLabel.textContent = 'Random';

        randomInput.addEventListener('change', () => {
            applyRandomToMultipleColumn(randomInput.dataset.fieldKey, randomInput.checked);
        });

        randomWrap.appendChild(randomInput);
        randomWrap.appendChild(randomLabel);

        headerWrap.appendChild(title);
        headerWrap.appendChild(randomWrap);
        th.appendChild(headerWrap);
        headRow.appendChild(th);
    });

    thead.appendChild(headRow);
    table.appendChild(thead);

    const tbody = document.createElement('tbody');

    for (let rowIndex = 0; rowIndex < count; rowIndex++) {
        const tr = document.createElement('tr');

        fields.forEach((field) => {
            const td = document.createElement('td');

            let input;
            if (field.type === 'select') {
                input = document.createElement('select');
                input.className = 'form-select form-select-sm';
                const defaultOption = document.createElement('option');
                defaultOption.value = '';
                defaultOption.textContent = 'Select...';
                input.appendChild(defaultOption);
                (field.options || []).forEach((opt) => {
                    const optionEl = document.createElement('option');
                    optionEl.value = opt;
                    optionEl.textContent = opt;
                    input.appendChild(optionEl);
                });
            } else if (field.type === 'textarea') {
                input = document.createElement('textarea');
                input.className = 'form-control form-control-sm';
                input.rows = 1;
            } else {
                input = document.createElement('input');
                input.className = 'form-control form-control-sm';
                input.type = field.type === 'number' ? 'number' : (field.type === 'email' ? 'email' : (field.type === 'url' ? 'url' : 'text'));
                if (field.type === 'number') input.step = '0.01';
            }

            input.placeholder = field.placeholder || '';
            input.required = Boolean(field.required);
            input.dataset.rowIndex = String(rowIndex);
            input.dataset.fieldKey = field.key;
            input.autocomplete = 'off';

            td.appendChild(input);
            tr.appendChild(td);
        });

        tbody.appendChild(tr);
    }

    table.appendChild(tbody);
    container.appendChild(table);
}

function clearMultipleTable() {
    const container = document.getElementById('multipleTableContainer');
    if (container) container.innerHTML = '';
}

function parseMultipleTablePayloads() {
    const table = document.getElementById('multiplePayloadTable');
    if (!table) return [];

    const rows = Array.from(table.querySelectorAll('tbody tr'));
    const payloads = [];

    rows.forEach((tr) => {
        const payload = {};
        const inputs = Array.from(tr.querySelectorAll('[data-field-key]'));
        inputs.forEach((el) => {
            const key = el.dataset.fieldKey;
            const raw = String(el.value ?? '').trim();
            if (raw === '') return;

            if (!isNaN(raw) && raw !== '' && el.tagName.toLowerCase() !== 'select' && el.type === 'number') {
                payload[key] = parseFloat(raw);
            } else if (raw === 'true') {
                payload[key] = true;
            } else if (raw === 'false') {
                payload[key] = false;
            } else {
                payload[key] = raw;
            }
        });

        payloads.push(payload);
    });

    return payloads;
}

function showPayloadPreview() {
    if (!currentService) {
        showAlert('Please select a service', 'warning');
        return;
    }

    const mode = document.querySelector('input[name="triggerMode"]:checked').value;

    try {
        if (mode === 'single') {
            const formEl = document.getElementById('singlePayloadForm');
            if (!formEl.checkValidity()) {
                formEl.reportValidity();
                return;
            }
            const overrides = collectSingleFormOverrides();
            const finalPayload = buildFinalPayloadForSingle(overrides);
            showAlert(`
                <div>
                    <strong>Payload Preview</strong><br>
                    <small class="text-muted d-block mt-2">
                        ${JSON.stringify(finalPayload, null, 2)}
                    </small>
                </div>
            `, 'info');
            return;
        }

        const payloads = parseMultipleTablePayloads();
        if (payloads.length === 0) {
            showAlert('Please build the table and fill values in Multiple mode', 'warning');
            return;
        }

        const requiredKeys = getRequiredFieldKeys(currentService);
        const missingByLine = payloads
            .map((p, idx) => ({ idx: idx + 1, missing: findMissingRequiredKeys(requiredKeys, p) }))
            .filter(x => x.missing.length > 0);
        if (missingByLine.length > 0) {
            showAlert(
                `Missing required fields in Multiple mode: ` +
                missingByLine.map(x => `line ${x.idx}: ${x.missing.join(', ')}`).join(' | '),
                'warning'
            );
            return;
        }

        const finalPayloads = buildFinalPayloadsForMultiple(payloads);
        showAlert(`
            <div>
                <strong>Payload Preview (${finalPayloads.length})</strong><br>
                <small class="text-muted d-block mt-2">
                    ${JSON.stringify(finalPayloads, null, 2)}
                </small>
            </div>
        `, 'info');
    } catch (error) {
        console.error('Preview error:', error);
        showAlert('Failed to build payload preview: ' + error.message, 'danger');
    }
}

// Trigger payload
async function triggerPayload() {
    if (!currentService) {
        showAlert('Please select a service', 'warning');
        return;
    }

    const mode = document.querySelector('input[name="triggerMode"]:checked').value;
    const triggerBtn = document.getElementById('triggerBtn');

    // Disable button and show loading
    triggerBtn.disabled = true;
    const originalHtml = triggerBtn.innerHTML;
    triggerBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Triggering...';

    try {
        if (mode === 'single') {
            await triggerSinglePayload();
        } else {
            await triggerMultiplePayloads();
        }
    } catch (error) {
        console.error('Error:', error);
        showAlert('Error triggering payload: ' + error.message, 'danger');
    } finally {
        triggerBtn.disabled = false;
        triggerBtn.innerHTML = originalHtml;
    }
}

// Trigger single payload
async function triggerSinglePayload() {
    const formEl = document.getElementById('singlePayloadForm');
    if (!formEl.checkValidity()) {
        formEl.reportValidity();
        return;
    }
    const payload = collectSingleFormOverrides();

    const requiredKeys = getRequiredFieldKeys(currentService);
    const missing = findMissingRequiredKeys(requiredKeys, payload);
    if (missing.length > 0) {
        showAlert(`Please fill required fields: ${missing.join(', ')}`, 'warning');
        return;
    }

    const response = await fetch('/api/trigger/single', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            serviceId: currentService.id,
            payload: payload
        })
    });

    const result = await response.json();

    if (response.ok) {
        showAlert(`
            <div>
                <strong>âœ“ Success!</strong><br>
                Payload sent to Event Hub: <code>${result.eventHubName}</code><br>
                <small class="text-muted d-block mt-2">
                    ${JSON.stringify(result.payload, null, 2)}
                </small>
            </div>
        `, 'success');
    } else {
        throw new Error(result.error || 'Unknown error');
    }
}

// Trigger multiple payloads
async function triggerMultiplePayloads() {
    const payloads = parseMultipleTablePayloads();

    if (payloads.length === 0) {
        showAlert('Please build the table and fill values', 'warning');
        return;
    }

    const requiredKeys = getRequiredFieldKeys(currentService);
    const missingByLine = payloads
        .map((p, idx) => ({ idx: idx + 1, missing: findMissingRequiredKeys(requiredKeys, p) }))
        .filter(x => x.missing.length > 0);
    if (missingByLine.length > 0) {
        showAlert(
            `Missing required fields: ` +
            missingByLine.map(x => `line ${x.idx}: ${x.missing.join(', ')}`).join(' | '),
            'warning'
        );
        return;
    }

    const response = await fetch('/api/trigger/multiple', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            serviceId: currentService.id,
            payloads: payloads
        })
    });

    const result = await response.json();

    if (response.ok) {
        const successCount = result.results.filter(r => r.success).length;
        showAlert(`
            <div>
                <strong>âœ“ Batch Triggered!</strong><br>
                ${successCount}/${result.results.length} payloads sent successfully<br>
                Event Hub: <code>${result.eventHubName}</code>
            </div>
        `, 'success');
    } else {
        throw new Error(result.error || 'Unknown error');
    }
}

// Parse multiple payloads from textarea
function parsePayloads(input) {
    const payloads = [];

    // Split by newline or comma, then parse each line
    const lines = input.split(/\n|,(?=[^,]*=)/);

    lines.forEach(line => {
        line = line.trim();
        if (!line) return;

        const payload = {};

        // Parse key=value pairs (keys can include dots for nested paths)
        const items = line.split(',');
        items.forEach(item => {
            const [key, ...valueParts] = item.split('=');
            if (key && valueParts.length > 0) {
                const value = valueParts.join('=').trim();
                payload[key.trim()] = isNaN(value) ? value : parseFloat(value);
            }
        });

        if (Object.keys(payload).length > 0) {
            payloads.push(payload);
        }
    });

    return payloads;
}

// Show alert message
function showAlert(message, type = 'info') {
    const alertDiv = document.getElementById('resultAlert');
    const icons = {
        success: 'bi-check-circle-fill',
        danger: 'bi-exclamation-circle-fill',
        warning: 'bi-exclamation-triangle-fill',
        info: 'bi-info-circle-fill'
    };

    alertDiv.className = `alert alert-${type}`;
    alertDiv.innerHTML = `
        <i class="bi ${icons[type]}"></i>
        <div>${message}</div>
    `;
    alertDiv.style.display = 'flex';

    // Auto-hide after 8 seconds if success
    if (type === 'success') {
        setTimeout(() => {
            alertDiv.style.display = 'none';
        }, 8000);
    }
}

function unlockAllInputs() {
    document.querySelectorAll('#singlePayloadForm input, #singlePayloadForm textarea').forEach(el => {
        el.readOnly = false;
    });
}

// Reset form
function resetForm() {
    const singleForm = document.getElementById('singlePayloadForm');
    singleForm.reset();
    unlockAllInputs();
    document.getElementById('multiplePayloadsInput').value = '';
    clearMultipleTable();
    document.getElementById('resultAlert').style.display = 'none';
    document.getElementById('singleMode').checked = true;
    switchMode('single');
}

// Close mode selector
function closeModeSelector() {
    document.getElementById('welcomeSection').style.display = 'block';
    document.getElementById('detailSection').style.display = 'none';
    document.querySelectorAll('.list-group-item').forEach(item => {
        item.classList.remove('active');
    });
    currentService = null;
}

// Utility: Show About
function showAbout() {
    const modal = new bootstrap.Modal(document.getElementById('aboutModal'));
    modal.show();
}

// Utility: Show Settings
function showSettings() {
    alert('Settings panel coming soon!');
}

// Utility: Clear Cache
function clearCache() {
    localStorage.clear();
    sessionStorage.clear();
    showAlert('Cache cleared successfully', 'success');
}
