require('dotenv').config();
const express = require('express');
const path = require('path');
const fs = require('fs');
const bodyParser = require('body-parser');
const http = require('http');
const { Server } = require('socket.io');
const axios = require('axios');
const session = require('express-session');
const { exec } = require('child_process');

const app = express();
const server = http.createServer(app);
const io = new Server(server);
const CONFIG_PATH = path.join(__dirname, '..', 'config', 'config.json');

function loadConfig() {
    return JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf-8'));
}

function saveConfig(config) {
    fs.writeFileSync(CONFIG_PATH, JSON.stringify(config, null, 2), 'utf-8');
}

app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());
app.use(session({
    secret: process.env.SESSION_SECRET || 'ildevbot_secret',
    resave: false,
    saveUninitialized: false,
    cookie: { 
        secure: false, 
        maxAge: 30 * 60 * 1000 // 30 minutes d'inactivité
    }
}));

// Middleware pour rafraîchir la session à chaque requête si actif
app.use((req, res, next) => {
    if (req.session) {
        req.session._garbage = Date();
        req.session.touch();
    }
    next();
});

// Config EJS
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Fichiers statiques (css/images)
app.use(express.static(path.join(__dirname, 'public')));

// Middleware de protection par mot de passe
function requireAuth(req, res, next) {
    if (req.session && req.session.authenticated) {
        return next();
    }
    res.redirect('/login');
}

// Page de login
app.get('/login', (req, res) => {
    res.render('login', { error: null });
});

app.post('/login', (req, res) => {
    const password = req.body.password;
    if (password === process.env.DASHBOARD_PASSWORD) {
        req.session.authenticated = true;
        res.redirect('/dashboard');
    } else {
        res.render('login', { error: 'Mot de passe incorrect.' });
    }
});

app.get('/logout', (req, res) => {
    req.session.destroy(() => {
        res.redirect('/login');
    });
});

// Protéger toutes les routes du dashboard sauf /login
app.use((req, res, next) => {
    if (req.path.startsWith('/login')) return next();
    if (req.path.startsWith('/public')) return next();
    if (req.path.startsWith('/socket.io')) return next();
    if (req.path === '/favicon.ico') return next();
    return requireAuth(req, res, next);
});

// Helper pour charger un JSON (synchrone ici pour simplifier)
function loadJSON(filepath) {
    try {
        return JSON.parse(fs.readFileSync(filepath, 'utf-8'));
    } catch (e) {
        return null;
    }
}

// Route principale

app.get('/', (req, res) => res.redirect('/dashboard'));

app.get('/dashboard', (req, res) => {
    const config = loadJSON(path.join(__dirname, '..', 'config', 'config.json')) || {};
    const open_trades = loadJSON(path.join(__dirname, '..', 'logs', 'open_trades.json')) || [];
    const last_signals = loadJSON(path.join(__dirname, '..', 'logs', 'last_signals.json')) || [];
    res.render('dashboard', { config, open_trades, last_signals, page: 'dashboard', message: req.query.message, error: req.query.error });
});

app.get('/trades', (req, res) => {
    const open_trades = loadJSON(path.join(__dirname, '..', 'logs', 'open_trades.json')) || [];
    res.render('trades', { open_trades, page: 'trades', message: req.query.message, error: req.query.error });
});

app.get('/journal', (req, res) => {
    const closed_trades = loadJSON(path.join(__dirname, '..', 'logs', 'closed_trades.json')) || [];
    const config = loadJSON(path.join(__dirname, '..', 'config', 'config.json')) || {};
    res.render('journal', { closed_trades, config, page: 'journal' });
});

app.get('/logs', (req, res) => {
    const logsDir = path.join(__dirname, '..', 'logs');
    let logContent = [];
    try {
        const logFiles = fs.readdirSync(logsDir).filter(f => f.endsWith('.log'));
        if (logFiles.length) {
            const latestLog = logFiles.map(f => ({
                name: f,
                time: fs.statSync(path.join(logsDir, f)).mtime.getTime()
            })).sort((a, b) => b.time - a.time)[0].name;
            const lines = fs.readFileSync(path.join(logsDir, latestLog), 'utf-8').split('\n');
            logContent = lines.slice(-50);
        }
    } catch (e) {
        logContent = [];
    }
    res.render('logs', { logContent, page: 'logs' });
});

app.get('/parametre', (req, res) => {
    const config = loadJSON(path.join(__dirname, '..', 'config', 'config.json')) || {};
    res.render('parametre', { config, page: 'parametre', message: req.query.message, error: req.query.error });
});

app.get('/guide', (req, res) => {
    res.render('guide', { page: 'guide' });
});

app.post('/pause', async (req, res) => {
    try {
        await axios.post('http://127.0.0.1:5005/pause', {}, {
            headers: { 'x-api-key': process.env.API_SECRET_KEY }
        });
        broadcastDashboardUpdate();
        res.redirect('/dashboard?message=Bot%20en%20pause');
    } catch (e) {
        res.redirect('/dashboard?error=Erreur%20API%20Python%20(pause)');
    }
});

app.post('/play', async (req, res) => {
    try {
        await axios.post('http://127.0.0.1:5005/play', {}, {
            headers: { 'x-api-key': process.env.API_SECRET_KEY }
        });
        broadcastDashboardUpdate();
        res.redirect('/dashboard?message=Bot%20activ%C3%A9');
    } catch (e) {
        res.redirect('/dashboard?error=Erreur%20API%20Python%20(play)');
    }
});

app.post('/reset', async (req, res) => {
    try {
        await axios.post('http://127.0.0.1:5005/reset', {}, {
            headers: { 'x-api-key': process.env.API_SECRET_KEY }
        });
        broadcastDashboardUpdate();
        res.redirect('/dashboard?message=Red%C3%A9marrage%20demand%C3%A9');
    } catch (e) {
        res.redirect('/dashboard?error=Erreur%20API%20Python%20(reset)');
    }
});
app.post('/toggle-break-even', (req, res) => {
    try {
        const config = loadConfig();
        config.break_even = config.break_even || {};
        config.break_even.enabled = !!req.body.enabled;
        saveConfig(config);

        broadcastDashboardUpdate();
        res.json({ ok: true });
    } catch (e) {
        res.status(500).json({ ok: false });
    }
});


app.post('/toggle-security', (req, res) => {
    try {
        const config = loadConfig();
        config.security = config.security || {};
        config.security.enabled = !!req.body.enabled;
        saveConfig(config);

        broadcastDashboardUpdate();
        res.json({ ok: true });
    } catch (e) {
        res.status(500).json({ ok: false });
    }
});


app.post('/close-trade', async (req, res) => {
    const ticket = req.body.ticket;
    try {
        await axios.post('http://127.0.0.1:5005/close-trade', { ticket }, {
            headers: { 'x-api-key': process.env.API_SECRET_KEY }
        });
        broadcastDashboardUpdate();
        const referer = req.headers.referer || '';
        if (referer.includes('/trades')) {
            res.redirect('/trades?message=Trade%20fermé');
        } else {
            res.redirect('/dashboard?message=Trade%20fermé');
        }
    } catch (e) {
        res.redirect('/dashboard?error=Erreur%20API%20Python%20(close-trade)');
    }
});

app.post('/parametre', (req, res) => {
    const configPath = path.join(__dirname, '..', 'config', 'config.json');
    let config = loadJSON(configPath) || {};
    // MAJ des champs principaux
    config.mt5_login = req.body.mt5_login || '';
    config.mt5_password = req.body.mt5_password || '';
    config.mt5_server = req.body.mt5_server || '';
    config.telegram_api_id = req.body.telegram_api_id || '';
    config.telegram_api_hash = req.body.telegram_api_hash || '';
    config.telegram_channel = req.body.telegram_channel ? req.body.telegram_channel.split(',').map(s => s.trim()).filter(Boolean) : [];
    config.telegram_session = req.body.telegram_session || '';
    config.mode = req.body.mode || 'mt5_trading';
    config.break_even_enabled = !!req.body.break_even_enabled;
    config.tp_mode = req.body.tp_mode || 'progressive';
    config.show_stats_on_exit = !!req.body.show_stats_on_exit;
    // Risques
    config.risk = config.risk || {};
    config.risk.max_lot = parseFloat(req.body.risk_max_lot) || 0.1;
    config.risk.max_daily_loss = parseFloat(req.body.risk_max_daily_loss) || 200;
    config.risk.max_open_trades = parseInt(req.body.risk_max_open_trades) || 10;
    config.risk.stop_loss_required = !!req.body.risk_stop_loss_required;
    config.risk.default_lot = parseFloat(req.body.risk_default_lot) || 0.05;
    config.risk.break_even_on_tp = !!req.body.risk_break_even_on_tp;
    config.risk.allowed_symbols = req.body.risk_allowed_symbols ? req.body.risk_allowed_symbols.split(',').map(s => s.trim()).filter(Boolean) : [];
    // Parser avancé
    config.signal_parser = config.signal_parser || {};
    config.signal_parser.symbol_pattern = req.body.parser_symbol_pattern || '';
    config.signal_parser.type_pattern = req.body.parser_type_pattern || '';
    config.signal_parser.tp_pattern = req.body.parser_tp_pattern || '';
    config.signal_parser.sl_pattern = req.body.parser_sl_pattern || '';
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2), 'utf-8');
    res.redirect('/parametre?message=Config%20sauvegard%C3%A9e%20avec%20succ%C3%A8s');
});

app.get('/api/dashboard', (req, res) => {
    const config = loadJSON(path.join(__dirname, '..', 'config', 'config.json')) || {};
    const open_trades = loadJSON(path.join(__dirname, '..', 'logs', 'open_trades.json')) || [];
    const last_signals = loadJSON(path.join(__dirname, '..', 'logs', 'last_signals.json')) || [];
    res.json({
        config,
        open_trades,
        last_signals
    });
});

// WebSocket : envoie les données dashboard à chaque connexion
io.on('connection', (socket) => {
    // Envoie les données initiales
    sendDashboardData(socket);
});

function sendDashboardData(socket) {
    const config = loadJSON(path.join(__dirname, '..', 'config', 'config.json')) || {};
    const open_trades = loadJSON(path.join(__dirname, '..', 'logs', 'open_trades.json')) || [];
    const last_signals = loadJSON(path.join(__dirname, '..', 'logs', 'last_signals.json')) || [];
    socket.emit('dashboard_update', { config, open_trades, last_signals });
}

// Fonction pour notifier tous les clients d'une mise à jour
function broadcastDashboardUpdate() {
    const config = loadJSON(path.join(__dirname, '..', 'config', 'config.json')) || {};
    const open_trades = loadJSON(path.join(__dirname, '..', 'logs', 'open_trades.json')) || [];
    const last_signals = loadJSON(path.join(__dirname, '..', 'logs', 'last_signals.json')) || [];
    io.emit('dashboard_update', { config, open_trades, last_signals });
}

app.post('/reset-logs', (req, res) => {
    const scriptPath = path.join(__dirname, '..', 'utils', 'reset_logs.py');
    exec(`python "${scriptPath}"`, (error, stdout, stderr) => {
        if (error) {
            console.error('Erreur lors de la réinitialisation des logs:', error, stderr);
            return res.redirect('/dashboard?error=Erreur%20lors%20de%20la%20r%C3%A9initialisation%20des%20logs');
        }
        console.log(stdout);
        res.redirect('/dashboard?message=Tous%20les%20journaux%20ont%20%C3%A9t%C3%A9%20r%C3%A9initialis%C3%A9s');
    });
});

// Lance le serveur
server.listen(3000, () => {
    console.log('Serveur lancé sur http://localhost:3000');
});
