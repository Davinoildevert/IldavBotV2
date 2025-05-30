// Rafraîchissement dynamique du dashboard
function updateDashboard() {
    fetch('/api/dashboard')
        .then(res => res.json())
        .then(data => {
            // Statut du bot
            const statusIcon = document.getElementById('bot-status-icon');
            const statusBtn = document.getElementById('bot-status-btn');
            const statusText = document.getElementById('bot-status-text');
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
            if (data.open_trades.length) {
                data.open_trades.forEach(trade => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${trade.symbol}</td>
                        <td>${trade.type}</td>
                        <td>${trade.lot}</td>
                        <td>${trade.entry}</td>
                        <td>${trade.sl}</td>
                        <td>${trade.tp}</td>
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
                row.innerHTML = `<td colspan="8" style="color:#bbb;">Aucune position ouverte pour le moment.</td>`;
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
        });
}

// Rafraîchit toutes les 5 secondes
setInterval(updateDashboard, 5000);
document.addEventListener('DOMContentLoaded', updateDashboard);

// Toasts dynamiques (messages de succès/erreur)
function showToast(msg, type='success') {
    let toast = document.createElement('div');
    toast.className = 'toast ' + (type === 'error' ? 'toast-error' : 'toast-success');
    toast.textContent = msg;
    document.body.appendChild(toast);
    setTimeout(() => { toast.remove(); }, 3000);
}
window.showToast = showToast;
