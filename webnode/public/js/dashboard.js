function updateRiskSummary(trades = []) {
    // ✅ Cas aucun trade (polish UX)
    if (!trades.length) {
        safeSetText('risk-percent', '⚠️ Risque engagé : 0%');
        safeSetText('risk-sl', '🔻 Perte max (SL) : 0');
        safeSetText('risk-secured', '🟢 Profit sécurisé : 0');
        safeSetText('risk-correlated', '🔗 Trades corrélés : 0');
        return;
    }

    let totalRisk = 0;
    let totalSL = 0;
    let secured = 0;

    trades.forEach(t => {
        totalRisk += Number(t.risk_percent || 0);
        totalSL   += Number(t.sl_loss || 0);

        if (t.break_even || t.tp_hit) {
            secured += Number(t.profit || 0);
        }
    });
document.getElementById('risk-percent')
    ?.classList.toggle('alert-warning', totalRisk > 3);


    safeSetText('risk-percent', `⚠️ Risque engagé : ${totalRisk.toFixed(2)}%`);
    safeSetText('risk-sl', `🔻 Perte max (SL) : ${totalSL.toFixed(2)}`);
    safeSetText('risk-secured', `🟢 Profit sécurisé : ${secured.toFixed(2)}`);
    safeSetText('risk-correlated', `🔗 Trades corrélés : ${trades.length}`);
}


function safeSetText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
}

function renderSignalFeedback(signals) {
    const container = document.getElementById('signal-feedback');
    if (!container) return;

    container.innerHTML = '';

    if (!signals || !signals.length) {
        container.innerHTML = '<div style="color:#bbb;">Aucune décision récente.</div>';
        return;
    }

   signals.slice(-5).reverse().forEach(sig => {
    let color = '#aaa';
    let icon = 'ℹ️';
    let reasonText = 'Décision inconnue';

    if (sig.status === 'executed') {
        color = '#4caf50';
        icon = '✅';
        reasonText = 'Trade exécuté avec succès';
    } else if (sig.status === 'ignored') {
        color = '#ffc107';
        icon = '⚠️';
        reasonText = 'Ignoré → cooldown actif';
    } else if (sig.status === 'blocked') {
        color = '#ff9800';
        icon = '⛔';
        reasonText = 'Bloqué → règles de sécurité';
    } else if (sig.status === 'rejected') {
        color = '#f44336';
        icon = '❌';
        reasonText = 'Rejeté → broker / lot / filling';
    }

    const div = document.createElement('div');
    div.style.marginBottom = '6px';
    div.style.color = color;
    div.innerHTML = `
        ${icon} <b>${sig.symbol || '?'} ${sig.type || ''}</b>

        → ${sig.reason || reasonText}
        <span style="font-size:0.85em;color:#777;">(${sig.time || '-'})</span>
    `;

    container.appendChild(div);
});

}
function getTradeBadge(trade) {
    if (trade.tp_hit) {
        return { text: '🔵 TP+', class: 'badge-tp' };
    }
    if (trade.break_even) {
        return { text: '🟢 BE', class: 'badge-be' };
    }
    if (!trade.sl) {
        return { text: '🔴 SL', class: 'badge-sl' };
    }
    return { text: '🟡 TP1', class: 'badge-wait' };
}


function updateBotGlobalStatus(config) {
    if (!config) return;
    const el = document.getElementById('status-enabled');
    if (!el) return; // sécurité DOM
    // Bot ON / OFF
    safeSetText(
        'status-enabled',
        config.enabled ? '🤖 Bot : ACTIF' : '🤖 Bot : PAUSE'
);


    // Sécurité
    const sec = config.security || {};
    safeSetText('status-security', sec.enabled ? '🔐 Sécurité : ON' : '🔓 Sécurité : OFF');


    // Break-even
    const be = config.break_even || {};
    if (be.enabled) {
        safeSetText(
        'status-be',
        `🎯 Break-even : ON (${be.trigger || 'tp1'})`
    );


    } else {
       
        safeSetText('status-be', '🎯 Break-even : OFF');

    }

    // TP mode
    safeSetText(
    'status-tp-mode',
    `📊 TP mode : ${config.tp_mode || 'progressive'}`
);


    // Cooldown
    const cooldown = sec.cooldown_seconds || 0;
    safeSetText('status-cooldown', `⏱ Cooldown : ${cooldown}s`);
    
document.getElementById('bot-global-status')
    ?.classList.toggle('alert-warning', !config.security?.enabled);

document.getElementById('status-be')
    ?.classList.toggle('alert-warning', !config.break_even?.enabled);


}

// Rafraîchissement dynamique du dashboard
function updateDashboard() {
    fetch('/api/dashboard')
        .then(res => res.ok ? res.json() : null)
       
        .then(data => {
            // Statut du bot
            const statusIcon = document.getElementById('bot-status-icon');
            const statusBtn = document.getElementById('bot-status-btn');
            const statusText = document.getElementById('bot-status-text');
            if (!data || !data.config) return;
            if (data.config.enabled) {
                statusIcon.textContent = '⏸️';
                statusBtn.form.action = '/pause';
                statusText.innerHTML = '<span class="active-dot">● ACTIF</span>';
            } else {
                statusIcon.textContent = '▶️';
                statusBtn.form.action = '/play';
                statusText.innerHTML = '<span style="color:#ff6464;font-weight:700;">● PAUSE</span>';
            }
            // Trades ouverts
            const tradesTable = document.getElementById('trades-table-body');
            tradesTable.innerHTML = '';
            if (data.open_trades && data.open_trades.length) {

                data.open_trades.forEach(trade => {
                    const row = document.createElement('tr');
                    const badge = getTradeBadge(trade);

                    row.innerHTML = `
                        <td>${trade.symbol}</td>
                        <td>${trade.type}</td>
                        <td>${trade.lot}</td>
                        <td>${trade.entry}</td>
                        <td>${trade.sl || '-'}</td>
                        <td>${trade.tp || '-'}</td>
                        <td>
                            <span class="trade-badge ${badge.class}">
                                ${badge.text}
                            </span>
                        </td>
                        <td>${trade.profit}</td>
                        <td>
                            <form method="POST" action="/close-trade" style="display:inline;">
                                <input type="hidden" name="ticket" value="${trade.ticket}">
                                <button class="custom-btn red" type="submit">❌ Fermer</button>
                            </form>
                        </td>
                    `;

                    tradesTable.appendChild(row);
                });
            } else {
                const row = document.createElement('tr');
                row.innerHTML = `<td colspan="9" style="color:#bbb;">Aucune position ouverte pour le moment.</td>`;
                tradesTable.appendChild(row);
            }
            // Derniers signaux
            const signalsDiv = document.getElementById('signals-list');
            signalsDiv.innerHTML = '';
            if (data.last_signals && data.last_signals.length) {
                data.last_signals.slice(-5).reverse().forEach(sig => {
                    const div = document.createElement('div');
                    div.style.marginBottom = '8px';
                    div.innerHTML = `<b>${sig.symbol} ${sig.type}</b> | Entrée: ${sig.entry || '-'} | SL: ${sig.sl || '-'} | TP: ${(Array.isArray(sig.tp) ? sig.tp.join(', ') : (sig.tp || '-'))}<div style="font-size:0.95em;color:#aaa;">Reçu le ${sig.time || '-'}</div>`;
                    signalsDiv.appendChild(div);
                });
            } else {
                signalsDiv.innerHTML = '<div style="color:#bbb;">Aucun signal récent détecté.</div>';
            }
            updateBotGlobalStatus(data.config);
            renderSignalFeedback(data.last_signals);
            updateRiskSummary(data.open_trades);


        });
}

// Rafraîchit toutes les 5 secondes
setInterval(() => {
    if (document.getElementById('trades-table-body')) {
        updateDashboard();
    }
}, 5000);



// Toasts dynamiques (messages de succès/erreur)
function showToast(msg, type='success') {
    let toast = document.createElement('div');
    toast.className = 'toast ' + (type === 'error' ? 'toast-error' : 'toast-success');
    toast.textContent = msg;
    document.body.appendChild(toast);
    setTimeout(() => { toast.remove(); }, 3000);
}
window.showToast = showToast;
function handleToggle(buttonId, endpoint, label) {
    const btn = document.getElementById(buttonId);
    if (!btn) return;

    btn.addEventListener('click', () => {
        // ⛔ anti double-clic
        if (btn.dataset.loading === 'true') return;
        btn.dataset.loading = 'true';
        const currentState = btn.dataset.state === 'on';
        const nextState = currentState ? 'off' : 'on';

        fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enabled: nextState === 'on' })
        })
        .then(res => {
            if (!res.ok) throw new Error('Erreur serveur');
            return res.json();
        })
        .then(() => {
            // UI update
            btn.dataset.state = nextState;
            const span = btn.querySelector('.toggle-state');
            if (span) span.textContent = nextState.toUpperCase();

            btn.classList.toggle('off', nextState === 'off');

            showToast(`${label} ${nextState === 'on' ? 'activé' : 'désactivé'}`);
        })
        .catch(() => {
            showToast(`Impossible de modifier ${label}`, 'error');
    
        
        })
        .finally(() => {
            // ✅ ré-autorise le clic
            btn.dataset.loading = 'false';
        });
        
    });
}
document.addEventListener('DOMContentLoaded', () => {
    updateDashboard();

    handleToggle(
        'toggle-be',
        '/toggle-break-even',
        'Break-even'
    );

    handleToggle(
        'toggle-security',
        '/toggle-security',
        'Sécurité'
    );
});
