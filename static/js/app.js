// ==============================================================================
// HỌC VIỆN CÔNG NGHỆ BƯU CHÍNH VIỄN THÔNG (PTIT)
// ĐỒ ÁN MÔN HỌC: CƠ SỞ DỮ LIỆU PHÂN TÁN
//
// Đề tài 105: Merkle Tree Log Integrity: "Immutable Audit Trail"
// Sinh viên thực hiện: Hồ Ngọc Hoàng Anh
// Mã số sinh viên: N23DCCN071
// Lớp: D23CQCN02-N
//
// Tệp tin: static/js/app.js - Xử lý logic hiển thị Dashboard, Merkle Tree và AJAX API
// ==============================================================================
document.addEventListener('DOMContentLoaded', () => {
    // State Variables
    let currentBlockId = 1;
    let selectedNodeHash = null;
    let treeData = null;
    let buildChartInstance = null;
    let overheadChartInstance = null;
    let nodePositions = []; // To store coordinates for hover detection
    let currentTamperedTxs = []; // To store currently detected tampered transactions for highlighting
    
    // UI Selectors
    const statusCoord = document.getElementById('status-coord');
    const statusA = document.getElementById('status-a');
    const statusB = document.getElementById('status-b');
    const statusTtp = document.getElementById('status-ttp');
    
    const transactionForm = document.getElementById('tx-form');
    const blockSelect = document.getElementById('block-select');
    const blockSelectAttack = document.getElementById('attack-block-select');
    const attackTxSelect = document.getElementById('attack-tx-select');
    const txTableBody = document.getElementById('tx-table-body');
    const treeCanvas = document.getElementById('tree-visual');
    const tooltip = document.getElementById('tree-tooltip');
    
    const attackForm = document.getElementById('attack-form');
    const attackAction = document.getElementById('attack-action');
    const amountGroup = document.getElementById('attack-amount-group');
    const attackAmount = document.getElementById('attack-amount');
    
    const btnAudit = document.getElementById('btn-audit');
    const auditLogs = document.getElementById('audit-logs');
    const auditAlertContainer = document.getElementById('audit-alert-container');
    const btnSeed = document.getElementById('btn-seed');
    const btnRunBenchmark = document.getElementById('btn-run-benchmark');
    
    // Adjust size of canvas
    function resizeCanvas() {
        const rect = treeCanvas.parentElement.getBoundingClientRect();
        treeCanvas.width = rect.width - 32;
        treeCanvas.height = 360;
        if (treeData) {
            drawTree(treeData);
        }
    }
    window.addEventListener('resize', resizeCanvas);

    // Initial load
    checkNodeHealth();
    loadBlockList();
    loadTransactions(1);
    loadBenchmarkCharts();
    resizeCanvas();
    
    // Check Health of Nodes
    async function checkNodeHealth() {
        try {
            const res = await fetch('/api/health');
            const data = await res.json();
            
            statusCoord.className = data.coord ? 'status-dot active' : 'status-dot error';
            statusA.className = data.a ? 'status-dot active' : 'status-dot error';
            statusB.className = data.b ? 'status-dot active' : 'status-dot error';
            statusTtp.className = data.ttp ? 'status-dot active' : 'status-dot error';
        } catch (err) {
            statusCoord.className = 'status-dot error';
            statusA.className = 'status-dot error';
            statusB.className = 'status-dot error';
            statusTtp.className = 'status-dot error';
        }
    }
    
    // Load lists of blocks for selects
    async function loadBlockList() {
        try {
            const res = await fetch('/api/ttp/hashes');
            const data = await res.json();
            
            blockSelect.innerHTML = '';
            blockSelectAttack.innerHTML = '<option value="">-- Chọn Block --</option>';
            
            let maxBlock = 1;
            if (data.length > 0) {
                data.forEach(bh => {
                    const blockId = bh.BlockID;
                    if (blockId > maxBlock) maxBlock = blockId;
                    
                    const opt = document.createElement('option');
                    opt.value = blockId;
                    opt.textContent = `Block ${blockId} (TXs: ${bh.StartTxID} - ${bh.EndTxID})`;
                    blockSelect.appendChild(opt);
                    
                    const opt2 = document.createElement('option');
                    opt2.value = blockId;
                    opt2.textContent = `Block ${blockId}`;
                    blockSelectAttack.appendChild(opt2);
                });
                
                const openBlock = maxBlock + 1;
                const opt = document.createElement('option');
                opt.value = openBlock;
                opt.textContent = `Block ${openBlock} (Đang mở)`;
                blockSelect.appendChild(opt);
                
                const opt2 = document.createElement('option');
                opt2.value = openBlock;
                opt2.textContent = `Block ${openBlock} (Đang mở)`;
                blockSelectAttack.appendChild(opt2);
            } else {
                const opt = document.createElement('option');
                opt.value = 1;
                opt.textContent = "Block 1 (Đang mở)";
                blockSelect.appendChild(opt);
                
                const opt2 = document.createElement('option');
                opt2.value = 1;
                opt2.textContent = "Block 1 (Đang mở)";
                blockSelectAttack.appendChild(opt2);
            }
            
            blockSelect.value = currentBlockId;
        } catch (err) {
            console.error("Failed to load block list:", err);
        }
    }
    
    // Load Transactions for a Block
    async function loadTransactions(blockId, tamperedTxs = []) {
        currentTamperedTxs = tamperedTxs;
        try {
            const res = await fetch(`/api/transactions?site=b&block_id=${blockId}`);
            if (!res.ok) {
                txTableBody.innerHTML = `<tr><td colspan="6" style="text-align:center; color: var(--text-secondary);">Chưa có giao dịch nào trong Block này.</td></tr>`;
                return;
            }
            const data = await res.json();
            txTableBody.innerHTML = '';
            
            if (data.length === 0) {
                txTableBody.innerHTML = `<tr><td colspan="6" style="text-align:center; color: var(--text-secondary);">Chưa có giao dịch nào trong Block này.</td></tr>`;
                return;
            }
            
            data.forEach((tx, idx) => {
                const tr = document.createElement('tr');
                
                const isTampered = tamperedTxs.includes(tx.TransactionID);
                if (isTampered) {
                    tr.className = 'tampered-row';
                }
                
                tr.innerHTML = `
                    <td>${idx + 1}</td>
                    <td class="tx-id-cell">${tx.TransactionID}</td>
                    <td>${tx.From_Account}</td>
                    <td>${tx.To_Account}</td>
                    <td class="amount-cell" style="color: ${isTampered ? '#ef4444' : (tx.Amount > 2000 ? 'var(--accent)' : 'var(--text-primary)')}">$${tx.Amount.toFixed(2)}</td>
                    <td><span class="block-badge">B-${tx.BlockID}</span></td>
                `;
                txTableBody.appendChild(tr);
            });
            
            loadMerkleTreeVisual(blockId);
        } catch (err) {
            console.error("Failed to load transactions:", err);
        }
    }
    
    // Load Merkle Tree Visual Layers
    async function loadMerkleTreeVisual(blockId) {
        try {
            const res = await fetch(`/api/merkle-tree/${blockId}?site=b`);
            if (!res.ok) {
                const ctx = treeCanvas.getContext('2d');
                ctx.clearRect(0, 0, treeCanvas.width, treeCanvas.height);
                ctx.fillStyle = '#94a3b8';
                ctx.font = '14px Outfit';
                ctx.textAlign = 'center';
                ctx.fillText('Không thể tạo sơ đồ Merkle Tree cho block đang mở.', treeCanvas.width / 2, treeCanvas.height / 2);
                treeData = null;
                return;
            }
            treeData = await res.json();
            drawTree(treeData);
        } catch (err) {
            console.error("Failed to fetch Merkle tree visual:", err);
        }
    }
    
    // Draw Merkle Tree using Canvas
    function drawTree(data) {
        const ctx = treeCanvas.getContext('2d');
        ctx.clearRect(0, 0, treeCanvas.width, treeCanvas.height);
        
        const layers = data.layers;
        const totalLayers = layers.length;
        
        nodePositions = [];
        
        const vSpace = treeCanvas.height / (totalLayers + 0.5);
        let layersCoords = [];
        
        for (let l = 0; l < totalLayers; l++) {
            const layerHashes = layers[l];
            const numNodes = layerHashes.length;
            const y = treeCanvas.height - (l + 1) * vSpace + (vSpace / 2);
            
            let layerCoords = [];
            for (let n = 0; n < numNodes; n++) {
                const x = (n + 0.5) * (treeCanvas.width / numNodes);
                layerCoords.push({ x, y, hash: layerHashes[n], layer: l, index: n });
                
                nodePositions.push({
                    x, y,
                    hash: layerHashes[n],
                    layer: l,
                    index: n,
                    radius: 8
                });
            }
            layersCoords.push(layerCoords);
        }
        
        // Tìm vị trí các giao dịch bị sửa đổi trong block hiện tại
        let tamperedIndices = [];
        if (currentTamperedTxs && currentTamperedTxs.length > 0 && data.transactions) {
            tamperedIndices = data.transactions
                .map((tx, index) => currentTamperedTxs.includes(tx.TransactionID) ? index : -1)
                .filter(index => index !== -1);
        }

        // Vẽ các đường nối giữa các tầng của cây Merkle
        ctx.lineWidth = 1.5;
        for (let l = totalLayers - 1; l > 0; l--) {
            const parents = layersCoords[l];
            const children = layersCoords[l - 1];
            
            for (let p = 0; p < parents.length; p++) {
                const parentNode = parents[p];
                const leftChildIdx = p * 2;
                const rightChildIdx = p * 2 + 1;
                
                // Kiểm tra xem nút cha có thuộc đường đi của giao dịch bị sửa đổi hay không
                let isParentTampered = false;
                for (const tIdx of tamperedIndices) {
                    if (p === (tIdx >> l)) {
                        isParentTampered = true;
                        break;
                    }
                }
                
                if (leftChildIdx < children.length) {
                    let isLeftChildTampered = false;
                    for (const tIdx of tamperedIndices) {
                        if (leftChildIdx === (tIdx >> (l - 1))) {
                            isLeftChildTampered = true;
                            break;
                        }
                    }
                    ctx.beginPath();
                    ctx.moveTo(parentNode.x, parentNode.y);
                    ctx.lineTo(children[leftChildIdx].x, children[leftChildIdx].y);
                    // Nếu cả cha và con đều thuộc đường đi bị sửa đổi, tô đường nối màu đỏ rực
                    ctx.strokeStyle = (isParentTampered && isLeftChildTampered) ? '#ef4444' : 'rgba(255, 255, 255, 0.08)';
                    ctx.stroke();
                }
                if (rightChildIdx < children.length) {
                    let isRightChildTampered = false;
                    for (const tIdx of tamperedIndices) {
                        if (rightChildIdx === (tIdx >> (l - 1))) {
                            isRightChildTampered = true;
                            break;
                        }
                    }
                    ctx.beginPath();
                    ctx.moveTo(parentNode.x, parentNode.y);
                    ctx.lineTo(children[rightChildIdx].x, children[rightChildIdx].y);
                    ctx.strokeStyle = (isParentTampered && isRightChildTampered) ? '#ef4444' : 'rgba(255, 255, 255, 0.08)';
                    ctx.stroke();
                }
            }
        }
        
        // Vẽ các nút tròn (Nodes)
        for (const node of nodePositions) {
            ctx.beginPath();
            ctx.arc(node.x, node.y, 7, 0, 2 * Math.PI);
            
            // Kiểm tra xem node này có thuộc đường dẫn băm bị ảnh hưởng không
            let isNodeTampered = false;
            for (const tIdx of tamperedIndices) {
                if (node.index === (tIdx >> node.layer)) {
                    isNodeTampered = true;
                    break;
                }
            }
            
            if (isNodeTampered) {
                ctx.fillStyle = '#ef4444'; // Đỏ rực cho node bị lỗi / bị ảnh hưởng
                ctx.shadowColor = '#ef4444';
            } else if (node.layer === totalLayers - 1) {
                ctx.fillStyle = '#d946ef'; // Gốc: Hồng/Tím
                ctx.shadowColor = '#d946ef';
            } else if (node.layer === 0) {
                ctx.fillStyle = '#06b6d4'; // Lá: Xanh ngọc
                ctx.shadowColor = '#06b6d4';
            } else {
                ctx.fillStyle = '#3b82f6'; // Thân: Xanh dương
                ctx.shadowColor = '#3b82f6';
            }
            
            ctx.shadowBlur = 4;
            ctx.fill();
            ctx.shadowBlur = 0;
            
            ctx.strokeStyle = isNodeTampered ? 'rgba(239, 68, 68, 0.8)' : 'rgba(255, 255, 255, 0.5)';
            ctx.lineWidth = 1;
            ctx.stroke();
        }
    }
    
    // Canvas Mouse Interactions
    treeCanvas.addEventListener('mousemove', (e) => {
        const rect = treeCanvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        let foundNode = null;
        for (const node of nodePositions) {
            const dist = Math.sqrt((x - node.x)**2 + (y - node.y)**2);
            if (dist <= node.radius + 4) {
                foundNode = node;
                break;
            }
        }
        
        if (foundNode) {
            treeCanvas.style.cursor = 'pointer';
            let tooltipX = x + 15;
            let tooltipY = y + 15;
            
            // Tự động dịch chuyển tooltip sang trái nếu ở quá sát mép phải
            if (x > treeCanvas.width - 280) {
                tooltipX = x - 290;
            }
            
            // Tự động dịch chuyển tooltip lên trên nếu ở quá sát mép dưới (tránh bị che mất thông tin)
            if (y > treeCanvas.height - 130) {
                tooltipY = y - 140;
            }
            
            tooltip.style.left = `${tooltipX}px`;
            tooltip.style.top = `${tooltipY}px`;
            
            let label = "";
            if (foundNode.layer === treeData.layers.length - 1) {
                label = "<strong>Merkle Root Hash</strong>";
            } else if (foundNode.layer === 0) {
                const tx = treeData.transactions[foundNode.index];
                label = `<strong>Leaf Hash (Tx: ${tx.TransactionID})</strong><br>From: ${tx.From_Account}<br>To: ${tx.To_Account}<br>Amount: $${tx.Amount.toFixed(2)}`;
            } else {
                label = `<strong>Internal Node (Lvl ${foundNode.layer}, Pos ${foundNode.index})</strong>`;
            }
            
            tooltip.innerHTML = `${label}<br><span style="color: #67e8f9; font-size: 0.7rem;">Hash: ${foundNode.hash}</span>`;
            tooltip.style.display = 'block';
        } else {
            treeCanvas.style.cursor = 'default';
            tooltip.style.display = 'none';
        }
    });
    
    treeCanvas.addEventListener('mouseleave', () => {
        tooltip.style.display = 'none';
    });

    // Select Block Event
    blockSelect.addEventListener('change', (e) => {
        currentBlockId = parseInt(e.target.value);
        loadTransactions(currentBlockId);
    });
    
    // Populate attack transaction list when block is chosen in attack simulator
    blockSelectAttack.addEventListener('change', async (e) => {
        const blockId = e.target.value;
        if (!blockId) {
            attackTxSelect.innerHTML = '<option value="">-- Chọn Giao dịch --</option>';
            return;
        }
        
        try {
            const res = await fetch(`/api/transactions?site=b&block_id=${blockId}`);
            const data = await res.json();
            attackTxSelect.innerHTML = '<option value="">-- Chọn Giao dịch --</option>';
            
            data.forEach(tx => {
                const opt = document.createElement('option');
                opt.value = tx.TransactionID;
                opt.textContent = `${tx.TransactionID} (${tx.From_Account} -> ${tx.To_Account}: $${tx.Amount})`;
                attackTxSelect.appendChild(opt);
            });
        } catch (err) {
            console.error("Failed to load txs for attack selection:", err);
        }
    });
    
    // Handle attack action visibility
    attackAction.addEventListener('change', (e) => {
        if (e.target.value === 'delete') {
            amountGroup.style.display = 'none';
        } else {
            amountGroup.style.display = 'block';
        }
    });
    
    // Submit Transaction Form
    transactionForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const fromAcc = document.getElementById('tx-from').value;
        const toAcc = document.getElementById('tx-to').value;
        const amount = document.getElementById('tx-amount').value;
        
        try {
            const res = await fetch('/api/transaction', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    From_Account: fromAcc,
                    To_Account: toAcc,
                    Amount: parseFloat(amount)
                })
            });
            
            const data = await res.json();
            if (res.ok) {
                alert(`Giao dịch thành công! ID: ${data.transaction.TransactionID}`);
                transactionForm.reset();
                
                await loadBlockList();
                
                if (data.block_completed) {
                    currentBlockId = data.block_completed;
                    blockSelect.value = currentBlockId;
                }
                
                loadTransactions(currentBlockId);
                checkNodeHealth();
            } else {
                alert(`Lỗi: ${data.error}`);
            }
        } catch (err) {
            alert(`Lỗi kết nối: ${err}`);
        }
    });
    
    // Submit Attack Form
    attackForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const action = attackAction.value;
        const blockId = blockSelectAttack.value;
        const txId = attackTxSelect.value;
        const amount = attackAmount.value;
        
        if (!action || !blockId) {
            alert("Vui lòng nhập đầy đủ thông tin.");
            return;
        }
        
        const payload = {
            Action: action,
            BlockID: parseInt(blockId)
        };
        
        if (action === 'modify' || action === 'delete') {
            if (!txId) {
                alert("Vui lòng chọn TransactionID để tấn công.");
                return;
            }
            payload.TransactionID = txId;
        }
        
        if (action === 'modify' || action === 'inject') {
            if (!amount) {
                alert("Vui lòng nhập số tiền.");
                return;
            }
            payload.Amount = parseFloat(amount);
        }
        
        try {
            const res = await fetch('http://127.0.0.1:5002/simulate-attack', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (res.ok) {
                alert(`TẤN CÔNG THÀNH CÔNG: ${data.message}`);
                currentBlockId = parseInt(blockId);
                blockSelect.value = currentBlockId;
                loadTransactions(currentBlockId);
                attackForm.reset();
                amountGroup.style.display = 'block';
                attackTxSelect.innerHTML = '<option value="">-- Chọn Giao dịch --</option>';
            } else {
                alert(`Thất bại: ${data.error}`);
            }
        } catch (err) {
            alert(`Lỗi kết nối: ${err}`);
        }
    });
    
    // Run Audit
    btnAudit.addEventListener('click', async () => {
        auditLogs.innerHTML = `<div class="audit-log-line">[i] Đang kết nối tới TTP để lấy Root Hash lưu trữ...</div>`;
        auditAlertContainer.innerHTML = '';
        
        try {
            const res = await fetch('/api/audit');
            const data = await res.json();
            
            setTimeout(() => {
                auditLogs.innerHTML += `<div class="audit-log-line">[i] Đang truy quét dữ liệu Site B. Quét qua ${data.checked_blocks} Blocks...</div>`;
            }, 300);
            
            setTimeout(() => {
                if (data.status === 'clean') {
                    auditLogs.innerHTML += `<div class="audit-log-line success">[+] KHÔNG PHÁT HIỆN THAY ĐỔI DỮ LIỆU. Hệ thống toàn vẹn!</div>`;
                    auditAlertContainer.innerHTML = `
                        <div class="alert-card" style="background: rgba(16, 185, 129, 0.08); border-color: var(--success); animation: none;">
                            <div class="alert-icon" style="color: var(--success); font-family: sans-serif;">✓</div>
                            <div class="alert-content">
                                <h3 style="color: #86efac;">Hệ thống an toàn</h3>
                                <p>Tất cả ${data.checked_blocks} block giao dịch khớp hoàn toàn với Root Hash lưu tại TTP.</p>
                            </div>
                        </div>
                    `;
                    loadTransactions(currentBlockId);
                } else {
                    auditLogs.innerHTML += `<div class="audit-log-line error">[!] PHÁT HIỆN SỬA ĐỔI DỮ LIỆU TẠI BLOCK: ${data.tampered_blocks.join(', ')}</div>`;
                    auditLogs.innerHTML += `<div class="audit-log-line error">[!] Đang kích hoạt giải thuật truy vết và điều tra số liệu...</div>`;
                    
                    let alertHtml = '';
                    let tamperedTxIds = [];
                    
                    data.forensics.forEach(forensic => {
                        const blockId = forensic.BlockID;
                        auditLogs.innerHTML += `<div class="audit-log-line warning">[-] Block ${blockId}: Root Hash TTP (${forensic.TTP_Root.substring(0,8)}...) != Local Root B (${forensic.SiteB_Root.substring(0,8)}...)</div>`;
                        
                        alertHtml += `
                            <div class="alert-card">
                                <div class="alert-icon">⚠</div>
                                <div class="alert-content" style="width: 100%;">
                                    <h3>PHÁT HIỆN INSIDER ATTACK - BLOCK ${blockId}</h3>
                                    <p>Root Hash của Site B không khớp với Root Hash bất biến tại TTP.</p>
                                    <table class="diff-table">
                                        <thead>
                                            <tr>
                                                <th>TransactionID</th>
                                                <th>Loại vi phạm</th>
                                                <th>Giá trị Site A (Sạch)</th>
                                                <th>Giá trị Site B (Bị sửa)</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                        `;
                        
                        forensic.Details.forEach(detail => {
                            tamperedTxIds.push(detail.TransactionID);
                            
                            let origStr = '-';
                            let modStr = '-';
                            
                            if (detail.Type === 'MODIFIED') {
                                const diffFields = Object.keys(detail.Diff).map(k => {
                                    const orig = detail.Diff[k].Original;
                                    const mod = detail.Diff[k].Modified;
                                    return `${k}: ${orig} -> ${mod}`;
                                }).join(', ');
                                
                                origStr = `$${detail.Original.Amount.toFixed(2)}`;
                                modStr = `$${detail.Modified.Amount.toFixed(2)} (${diffFields})`;
                            } else if (detail.Type === 'DELETED') {
                                origStr = `$${detail.Original.Amount.toFixed(2)} (Từ ${detail.Original.From_Account})`;
                                modStr = `<span style="color: var(--error);">[Bị xóa]</span>`;
                            } else if (detail.Type === 'INJECTED') {
                                origStr = `<span style="color: var(--success);">[Không có]</span>`;
                                modStr = `$${detail.Modified.Amount.toFixed(2)} (Bơm vào)`;
                            } else if (detail.Type === 'ROW_COUNT_MISMATCH') {
                                origStr = `Count: ${detail.Original.row_count}`;
                                modStr = `<span style="color: var(--error);">Count: ${detail.Modified.row_count}</span> (${detail.Diff.status})`;
                            }
                            
                            alertHtml += `
                                <tr>
                                    <td style="font-family: var(--font-mono); color: var(--primary);">${detail.TransactionID}</td>
                                    <td style="color: var(--warning); font-weight:600;">${detail.Type}</td>
                                    <td>${origStr}</td>
                                    <td>${modStr}</td>
                                </tr>
                            `;
                        });
                        
                        alertHtml += `
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        `;
                    });
                    
                    auditAlertContainer.innerHTML = alertHtml;
                    loadTransactions(currentBlockId, tamperedTxIds);
                }
            }, 600);
            
        } catch (err) {
            auditLogs.innerHTML += `<div class="audit-log-line error">[x] Lỗi: ${err}</div>`;
        }
    });

    // Seed Data trigger via Web GUI
    btnSeed.addEventListener('click', async () => {
        btnSeed.disabled = true;
        btnSeed.textContent = 'Đang khởi tạo dữ liệu...';
        auditLogs.innerHTML += `<div class="audit-log-line">[i] Bắt đầu khởi tạo 500 giao dịch mẫu trên localhost...</div>`;
        
        try {
            // For seeding via API in Node mode, coordinator can trigger or we can run generator via server API,
            // but running the generator locally writes to the files site_a.db and site_b.db directly!
            // Wait, we can implement a coordinator API `/api/seed` that runs the generator, or coordinator can just write
            // them using a small function. Let's make Coordinator have a seeding function or we can trigger it.
            // Let's implement an endpoint `/api/seed` in coordinator or run generator.
            // Wait, since generator writes to files, running a fetch to `/api/seed` on coordinator which imports the generator is easiest!
            // Let's make sure `/api/seed` is supported.
            // Wait, let's look at coordinator.py. Does it have `/api/seed`? We haven't added it yet.
            // Let's write a replace block to add `/api/seed` to coordinator.py later, or let coordinator handle seed.
            // Let's write a simple fetch to `/api/seed` in js.
            const res = await fetch('/api/seed', { method: 'POST' });
            const data = await res.json();
            if (res.ok) {
                alert("Khởi tạo 500 giao dịch (5 blocks) thành công!");
                auditLogs.innerHTML += `<div class="audit-log-line success">[+] Đã nạp thành công 500 giao dịch mẫu (5 blocks)!</div>`;
                await loadBlockList();
                currentBlockId = 1;
                blockSelect.value = 1;
                loadTransactions(1);
            } else {
                alert(`Lỗi: ${data.error}`);
            }
        } catch (err) {
            alert(`Lỗi kết nối: ${err}`);
        } finally {
            btnSeed.disabled = false;
            btnSeed.textContent = 'Init Seed Data (500 TXs)';
        }
    });
    
    // Run Benchmark trigger via Web GUI
    btnRunBenchmark.addEventListener('click', async () => {
        btnRunBenchmark.disabled = true;
        btnRunBenchmark.textContent = 'Đang chạy Benchmark...';
        auditLogs.innerHTML += `<div class="audit-log-line">[i] Đang khởi chạy hiệu năng Merkle Tree...</div>`;
        
        try {
            const res = await fetch('/api/benchmark', { method: 'POST' });
            const data = await res.json();
            if (res.ok) {
                alert("Chạy Benchmark thành công!");
                auditLogs.innerHTML += `<div class="audit-log-line success">[+] Chạy Benchmark thành công! Đang tải lại đồ thị...</div>`;
                loadBenchmarkCharts();
            } else {
                alert(`Lỗi: ${data.error}`);
            }
        } catch (err) {
            alert(`Lỗi kết nối: ${err}`);
        } finally {
            btnRunBenchmark.disabled = false;
            btnRunBenchmark.textContent = 'Run Performance Benchmarks';
        }
    });
    
    // Load Performance Profile Charts
    async function loadBenchmarkCharts() {
        try {
            const res = await fetch('/static/benchmark_results.json');
            if (!res.ok) {
                console.log("No benchmark json found yet.");
                return;
            }
            const data = await res.json();
            
            const sizes = data.map(d => d.BlockSize);
            const buildTimes = data.map(d => d.BuildTimeMs);
            const overheads = data.map(d => d.OverheadPct);
            
            // Build Time Chart
            const ctxBuild = document.getElementById('chart-build').getContext('2d');
            if (buildChartInstance) buildChartInstance.destroy();
            buildChartInstance = new Chart(ctxBuild, {
                type: 'line',
                data: {
                    labels: sizes,
                    datasets: [{
                        label: 'Build Time (ms)',
                        data: buildTimes,
                        borderColor: '#06b6d4',
                        backgroundColor: 'rgba(6, 182, 212, 0.1)',
                        borderWidth: 2,
                        tension: 0.3,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            grid: { color: 'rgba(255, 255, 255, 0.05)' },
                            ticks: { color: '#94a3b8' }
                        },
                        x: {
                            grid: { color: 'rgba(255, 255, 255, 0.05)' },
                            ticks: { color: '#94a3b8' }
                        }
                    },
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
            
            // Overhead Chart
            const ctxOverhead = document.getElementById('chart-overhead').getContext('2d');
            if (overheadChartInstance) overheadChartInstance.destroy();
            overheadChartInstance = new Chart(ctxOverhead, {
                type: 'line',
                data: {
                    labels: sizes,
                    datasets: [{
                        label: 'Storage Overhead (%)',
                        data: overheads,
                        borderColor: '#d946ef',
                        backgroundColor: 'rgba(217, 70, 239, 0.1)',
                        borderWidth: 2,
                        tension: 0.3,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            grid: { color: 'rgba(255, 255, 255, 0.05)' },
                            ticks: { color: '#94a3b8' }
                        },
                        x: {
                            grid: { color: 'rgba(255, 255, 255, 0.05)' },
                            ticks: { color: '#94a3b8' }
                        }
                    },
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
            
        } catch (err) {
            console.error("Failed to load benchmark charts:", err);
        }
    }
});
