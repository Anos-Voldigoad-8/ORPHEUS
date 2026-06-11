/* ============================================================
   ORPHEUS — Core Application Logic
   WebSocket, Voice, Chat, Dashboard, Routing
   ============================================================ */

(function () {
  'use strict';

  // ── State ──
  const state = {
    currentView: 'dashboard',
    wsConnected: false,
    voiceListening: false,
    commandHistory: [],
    historyIndex: -1,
    chatMessages: [],
    metrics: { cpu: 0, ram: 0, disk: 0, uptime: '0s' },
    agents: {},
    activityLog: [],
    particleSystem: null,
    settings: {
      voice: false,
      tts: true,
      scanlines: true,
      particles: true,
      reconnect: true
    },
    role: 'guest'
  };

  // ── DOM Cache ──
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => document.querySelectorAll(sel);

  // ── WebSocket ──
  let ws = null;
  let wsReconnectTimer = null;
  let wsReconnectDelay = 1000;

  function connectWebSocket() {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url = `${protocol}//${location.host}/ws`;

    updateConnectionStatus('connecting');
    log('system', 'Establishing neural link...');

    ws = new WebSocket(url);

    ws.onopen = () => {
      state.wsConnected = true;
      wsReconnectDelay = 1000;
      updateConnectionStatus('online');
      log('success', 'Neural link established. ORPHEUS online.');

      // Request initial data
      wsSend({ type: 'get_status' });
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleWSMessage(data);
      } catch (e) {
        console.error('WS parse error:', e);
      }
    };

    ws.onclose = () => {
      state.wsConnected = false;
      updateConnectionStatus('offline');
      log('error', 'Neural link severed. Reconnecting...');

      // Auto-reconnect with exponential backoff if setting is enabled
      if (state.settings.reconnect) {
        wsReconnectTimer = setTimeout(() => {
          wsReconnectDelay = Math.min(wsReconnectDelay * 1.5, 10000);
          connectWebSocket();
        }, wsReconnectDelay);
      }
    };

    ws.onerror = () => {
      log('error', 'WebSocket connection error.');
    };
  }

  function wsSend(data) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(data));
    }
  }

  function handleWSMessage(data) {
    switch (data.type) {
      case 'metrics':
        updateMetrics(data.payload);
        break;
      case 'agent_update':
        updateAgentStatus(data.payload);
        break;
      case 'command_response':
        receiveResponse(data.payload);
        break;
      case 'command_start':
        showTypingIndicator(true);
        if (state.particleSystem) state.particleSystem.setState('thinking');
        break;
      case 'command_complete':
        showTypingIndicator(false);
        if (state.particleSystem) {
          state.particleSystem.setState('active');
          state.particleSystem.pulse();
          setTimeout(() => state.particleSystem.setState('idle'), 2000);
        }
        break;
      case 'log':
        log(data.level || 'info', data.message);
        break;
      case 'activity':
        addActivity(data.payload);
        break;
      case 'file_list':
        updateFileList(data.payload);
        break;
      case 'status':
        if (data.payload.metrics) updateMetrics(data.payload.metrics);
        if (data.payload.agents) updateAgentStatus(data.payload.agents);
        break;
      case 'auth_info':
        state.role = data.payload.role;
        applyRoleRestrictions();
        break;
      case 'error':
        log('error', data.message || 'Unknown error');
        if (state.particleSystem) {
          state.particleSystem.setState('error');
          setTimeout(() => state.particleSystem.setState('idle'), 3000);
        }
        break;
    }
  }

  // ── Connection Status ──
  function updateConnectionStatus(status) {
    const dot = $('.status-indicator');
    const label = $('.status-label');
    if (dot) {
      dot.className = 'status-indicator';
      if (status === 'offline') dot.classList.add('offline');
      if (status === 'connecting') dot.classList.add('connecting');
    }
    if (label) {
      const labels = { online: 'ONLINE', offline: 'OFFLINE', connecting: 'LINKING...' };
      label.textContent = labels[status] || 'UNKNOWN';
    }
  }

  function applyRoleRestrictions() {
    const navChat = $('#nav-chat');
    const navFiles = $('#nav-files');
    const roleText = $('.user-info__role');
    const nameText = $('.user-info__name');
    const profileSettingsGroup = $('#profile-settings-group');

    if (state.role === 'guest') {
      if (navChat) navChat.style.display = 'none';
      if (navFiles) navFiles.style.display = 'none';
      if (roleText) roleText.textContent = 'GUEST ACCESS';
      if (nameText) nameText.textContent = 'Visitor';
      if (profileSettingsGroup) profileSettingsGroup.style.display = 'none';
      switchView('overview');
    } else if (state.role === 'user') {
      if (navFiles) navFiles.style.display = 'none';
      if (roleText) roleText.textContent = 'USER ACCESS';
      switchView('chat');
    } else if (state.role === 'admin') {
      if (navChat) navChat.style.display = '';
      if (navFiles) navFiles.style.display = '';
      if (roleText) roleText.textContent = 'ADMIN ACCESS';
      switchView('overview');
    }
  }

  // ── Profile Management ──
  let currentAvatarSelection = 'A';
  const avatarList = ['A', 'Goku', 'Gohan', 'Vegeta', 'Bulma', 'Rangiku', 'Yoruichi', 'Tsunade', 'Itachi', 'Jiraiya', 'Naruto', 'Hinata', 'Ichigo', 'Orihime', 'Aizen', 'Luffy', 'Zoro', 'Boa Hancock', 'Robin', 'Nami', 'Sanji'];

  function initAvatarSelector() {
      const container = $('#avatar-selector-container');
      if (!container || container.children.length > 0) return;
      
      avatarList.forEach(name => {
         const img = document.createElement('img');
         img.className = 'avatar-option';
         if(name === 'A') {
             img.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="60" height="60"><rect width="60" height="60" fill="%231f2937"/><text x="30" y="40" font-family="sans-serif" font-size="30" fill="white" text-anchor="middle">A</text></svg>';
         } else {
             img.src = `/ui/assets/avatars/${name.replace(/ /g, '_')}.jpg`;
         }
         img.title = name;
         img.dataset.avatar = name;
         img.addEventListener('click', () => {
             document.querySelectorAll('.avatar-option').forEach(el => el.classList.remove('selected'));
             img.classList.add('selected');
             currentAvatarSelection = name;
         });
         container.appendChild(img);
      });
  }

  async function loadProfile() {
    initAvatarSelector();
    try {
      const res = await fetch('/api/profile');
      if (res.ok) {
        const profile = await res.json();
        const nameInput = $('#setting-profile-name');
        if(nameInput) nameInput.value = profile.name || '';
        currentAvatarSelection = profile.avatar || 'A';
        const themeToggle = $('#setting-profile-theme');
        if(themeToggle) themeToggle.checked = (profile.theme === 'light');
        applyProfile(profile);
      }
    } catch (e) {
      console.error('Failed to load profile', e);
    }
  }

  function applyProfile(profile) {
    state.profile = profile;
    const nameEl = $('.user-info__name');
    const avatarEl = $('.user-avatar');
    
    if (nameEl) nameEl.textContent = profile.name;
    
    if (avatarEl) {
      const initial = profile.avatar.substring(0, 1).toUpperCase();
      const animeAvatars = {
        "Goku": "🐉", "Gohan": "👓", "Vegeta": "💥", "Bulma": "🔧", 
        "Rangiku": "🌸", "Yoruichi": "🐈‍⬛", "Tsunade": "🐌", "Itachi": "👁️", 
        "Jiraiya": "🐸", "Naruto": "🦊", "Hinata": "👁️‍🗨️", "Ichigo": "🍓", 
        "Orihime": "🧚", "Aizen": "🦋", "Luffy": "👒", "Zoro": "⚔️", 
        "Boa Hancock": "🐍", "Robin": "📖", "Nami": "🍊", "Sanji": "🚬"
      };
      if (animeAvatars[profile.avatar]) {
        avatarEl.textContent = animeAvatars[profile.avatar];
      } else if (profile.avatar !== 'A') {
        avatarEl.textContent = initial;
      } else {
        avatarEl.textContent = profile.name.substring(0, 1).toUpperCase();
      }
    }
    
    // Theme
    if (profile.theme === 'light') {
      document.body.classList.add('light-theme');
    } else {
      document.body.classList.remove('light-theme');
    }

    // Populate Settings UI
    
    document.querySelectorAll('.avatar-option').forEach(el => {
        el.classList.toggle('selected', el.dataset.avatar === currentAvatarSelection);
    });
  }

  async function saveProfile() {
    const nameInput = $('#setting-profile-name').value;
    const avatarSelect = currentAvatarSelection;
    const themeToggle = $('#setting-profile-theme').checked ? 'light' : 'dark';
    
    const btnSaveProfile = $('#btn-save-profile');
    if (btnSaveProfile) {
        btnSaveProfile.disabled = true;
        btnSaveProfile.textContent = "SAVING...";
    }

    const msgEl = $('#profile-save-message') || document.createElement('div');

    try {
      const res = await fetch('/api/profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: nameInput, avatar: avatarSelect, theme: themeToggle })
      });
      if (res.ok) {
        if(msgEl) {
            msgEl.textContent = "Profile saved successfully!";
            msgEl.style.color = "var(--green)";
        }
        applyProfile({ name: nameInput, avatar: avatarSelect, theme: themeToggle });
        loadProfile();
      } else {
        const data = await res.json();
        if(msgEl) {
            msgEl.textContent = data.message || "Failed to save profile.";
            msgEl.style.color = "var(--red)";
        }
      }
    } catch (e) {
      if(msgEl) {
          msgEl.textContent = "Network error while saving.";
          msgEl.style.color = "var(--red)";
      }
    } finally {
      if (btnSaveProfile) {
          btnSaveProfile.disabled = false;
          btnSaveProfile.textContent = "SAVE PROFILE";
      }
    }
  }


  // ── View Routing ──
  function switchView(viewName) {
    state.currentView = viewName;

    // Update nav
    $$('.nav-item').forEach((item) => {
      item.classList.toggle('active', item.dataset.view === viewName);
    });

    // Update views
    $$('.view').forEach((view) => {
      view.classList.toggle('active', view.id === `view-${viewName}`);
    });

    // Special actions per view
    if (viewName === 'files') {
      wsSend({ type: 'list_files' });
    }
  }

  // ── Dashboard Metrics ──
  function updateMetrics(metrics) {
    state.metrics = { ...state.metrics, ...metrics };

    const setValue = (id, value) => {
      const el = document.getElementById(id);
      if (el) el.textContent = value;
    };

    setValue('metric-cpu', `${parseFloat(metrics.cpu || 0).toFixed(1)}%`);
    setValue('metric-ram', `${parseFloat(metrics.ram || 0).toFixed(1)}%`);
    setValue('metric-disk', `${parseFloat(metrics.disk || 0).toFixed(1)}%`);
    setValue('metric-uptime', metrics.uptime || '—');

    // Update sub-text
    const cpuSub = document.getElementById('metric-cpu-sub');
    if (cpuSub && metrics.cpu_count) {
      cpuSub.textContent = `${metrics.cpu_count} cores`;
    }
    const ramSub = document.getElementById('metric-ram-sub');
    if (ramSub && metrics.ram_used && metrics.ram_total) {
      ramSub.textContent = `${metrics.ram_used} / ${metrics.ram_total}`;
    }
  }

  // ── Agent Status ──
  function updateAgentStatus(agents) {
    state.agents = agents;

    Object.entries(agents).forEach(([name, info]) => {
      const dot = document.querySelector(`.agent-card[data-agent="${name}"] .agent-dot`);
      if (dot) {
        dot.className = 'agent-dot';
        if (info.status === 'busy') dot.classList.add('busy');
        if (info.status === 'idle') dot.classList.add('idle');
      }

      // Update stats in agent detail view
      const taskEl = document.querySelector(`.agent-detail-card[data-agent="${name}"] .agent-tasks-val`);
      if (taskEl && info.tasks !== undefined) {
        taskEl.textContent = info.tasks;
      }
    });
  }

  // ── Chat ──
  function sendCommand(text) {
    if (!text.trim()) return;

    if (text.trim().toLowerCase() === '/clear') {
      const container = $('#chat-messages');
      if (container) container.innerHTML = '';
      state.chatMessages = [];
      addChatMessage('orpheus', 'Chat history cleared.');
      return;
    }

    // Add user message
    addChatMessage('user', text);

    // Add to history
    state.commandHistory.unshift(text);
    state.historyIndex = -1;

    // Show typing
    showTypingIndicator(true);

    // Send via WebSocket
    wsSend({
      type: 'command',
      command: text,
    });

    // Add activity
    addActivity({
      icon: '⚡',
      iconClass: 'cmd',
      text: `Command: ${text.substring(0, 60)}${text.length > 60 ? '...' : ''}`,
    });

    // Pulse the particle system
    if (state.particleSystem) {
      state.particleSystem.setState('thinking');
    }
  }

  function receiveResponse(payload) {
    showTypingIndicator(false);

    const text = typeof payload === 'string' ? payload : payload.result || payload.message || JSON.stringify(payload);
    addChatMessage('orpheus', text);

    // Speak it if voice is available and TTS setting is on
    if (state.settings.tts && window.speechSynthesis) {
      // Don't speak if response is massive JSON
      if (text.length < 500) {
        speak(text.replace(/[#*`_]/g, '').trim());
      }
    }
  }

  function addChatMessage(sender, text) {
    const container = $('#chat-messages');
    if (!container) return;

    const now = new Date();
    const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const msg = document.createElement('div');
    msg.className = `chat-msg ${sender}`;

    const avatarContent = sender === 'orpheus' ? '🔮' : '👤';

    // Simple markdown-like rendering
    let rendered = escapeHtml(text)
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br>');

    msg.innerHTML = `
      <div class="chat-msg__avatar">${avatarContent}</div>
      <div>
        <div class="chat-msg__bubble">${rendered}</div>
        <div class="chat-msg__time">${timeStr}</div>
      </div>
    `;

    container.appendChild(msg);
    // Smooth scroll to bottom
    container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });

    state.chatMessages.push({ sender, text, time: now });
  }

  function showTypingIndicator(show) {
    const indicator = $('.typing-indicator');
    if (indicator) {
      indicator.classList.toggle('active', show);
    }
  }

  // ── Voice (Web Speech API) ──
  let recognition = null;

  function initVoice() {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      log('warn', 'Voice not supported in this browser. Use Chrome or Edge.');
      return false;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onresult = (event) => {
      let finalTranscript = '';
      let interimTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript;
        } else {
          interimTranscript += transcript;
        }
      }

      // Show interim in input
      const input = $('#chat-input');
      if (interimTranscript && input) {
        input.value = interimTranscript;
      }

      if (finalTranscript) {
        if (input) input.value = '';
        sendCommand(finalTranscript.trim());
        log('info', `Voice: "${finalTranscript.trim()}"`);
      }
    };

    recognition.onend = () => {
      // Restart if still in listening mode
      if (state.voiceListening) {
        try {
          recognition.start();
        } catch (e) { /* ignore */ }
      }
    };

    recognition.onerror = (event) => {
      if (event.error !== 'no-speech' && event.error !== 'aborted') {
        log('error', `Voice error: ${event.error}`);
      }
    };

    return true;
  }

  function toggleVoice() {
    const btn = $('.btn-voice');
    if (!recognition && !initVoice()) {
      showToast('Voice not supported. Use Chrome or Edge.');
      return;
    }

    state.voiceListening = !state.voiceListening;

    if (state.voiceListening) {
      try {
        recognition.start();
        btn?.classList.add('listening');
        log('success', 'Voice activated. Listening...');
        showToast('🎤 Voice activated — speak your commands');
      } catch (e) {
        log('error', 'Failed to start voice recognition.');
        state.voiceListening = false;
      }
    } else {
      recognition.stop();
      btn?.classList.remove('listening');
      log('info', 'Voice deactivated.');
    }
  }

  function speak(text) {
    if (!window.speechSynthesis) return;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1;
    utterance.pitch = 0.9;
    utterance.volume = 0.8;

    // Try to pick a good voice
    const voices = window.speechSynthesis.getVoices();
    const preferred = voices.find(v => v.name.includes('Google') && v.lang.startsWith('en')) ||
                      voices.find(v => v.lang.startsWith('en'));
    if (preferred) utterance.voice = preferred;

    window.speechSynthesis.speak(utterance);
  }

  // ── Activity Feed ──
  function addActivity(item) {
    const container = $('#activity-feed');
    if (!container) return;

    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

    const el = document.createElement('div');
    el.className = 'activity-item';
    el.innerHTML = `
      <div class="activity-item__icon ${item.iconClass || ''}">${item.icon || '📡'}</div>
      <div class="activity-item__content">
        <div class="activity-item__text">${escapeHtml(item.text || '')}</div>
        <div class="activity-item__time">${now}</div>
      </div>
    `;

    container.prepend(el);

    // Keep max 50 items
    while (container.children.length > 50) {
      container.removeChild(container.lastChild);
    }

    state.activityLog.unshift({ ...item, time: now });
  }

  // ── Console Log ──
  function log(level, message) {
    const container = $('#console-log-body');
    if (!container) return;

    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

    const line = document.createElement('div');
    line.className = 'log-line';
    line.innerHTML = `
      <span class="log-time">${now}</span>
      <span class="log-level ${level}">[${level.toUpperCase()}]</span>
      <span class="log-msg">${escapeHtml(message)}</span>
    `;

    container.appendChild(line);
    container.scrollTop = container.scrollHeight;

    // Keep max 200 lines
    while (container.children.length > 200) {
      container.removeChild(container.firstChild);
    }
  }

  // ── File List ──
  function updateFileList(files) {
    const container = $('#file-list');
    if (!container) return;

    if (!files || files.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-state__icon">📁</div>
          <div class="empty-state__title">EMPTY WORKSPACE</div>
          <div class="empty-state__text">No files in workspace yet.</div>
        </div>
      `;
      return;
    }

    container.innerHTML = files.map(f => `
      <div class="file-item" onclick="window.orpheus.readFile('${escapeHtml(f.name)}')">
        <span class="file-item__icon">${f.is_dir ? '📁' : '📄'}</span>
        <span class="file-item__name">${escapeHtml(f.name)}</span>
        <span class="file-item__size">${f.size || ''}</span>
      </div>
    `).join('');
  }

  // ── Toast Notifications ──
  function showToast(message, duration = 3000) {
    const container = $('.toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
      toast.classList.add('leaving');
      setTimeout(() => toast.remove(), 300);
    }, duration);
  }

  // ── Clock ──
  function updateClock() {
    const el = $('#header-clock');
    if (el) {
      const now = new Date();
      el.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    }
  }

  // ── Utilities ──
  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // ── Settings Manager ──
  function initSettings() {
    // Load from local storage
    const saved = localStorage.getItem('orpheus_settings');
    if (saved) {
      try {
        state.settings = { ...state.settings, ...JSON.parse(saved) };
      } catch (e) { console.error('Failed to parse settings'); }
    }

    // Bind checkboxes
    const binds = {
      'setting-voice': 'voice',
      'setting-tts': 'tts',
      'setting-scanlines': 'scanlines',
      'setting-particles': 'particles',
      'setting-reconnect': 'reconnect'
    };

    Object.entries(binds).forEach(([id, key]) => {
      const el = document.getElementById(id);
      if (el) {
        el.checked = state.settings[key];
        el.addEventListener('change', (e) => {
          state.settings[key] = e.target.checked;
          localStorage.setItem('orpheus_settings', JSON.stringify(state.settings));
          applySettings();
        });
      }
    });

    applySettings();
  }

  function applySettings() {
    // Scanlines
    const scanlines = document.querySelector('.scanline-overlay');
    if (scanlines) scanlines.style.display = state.settings.scanlines ? 'block' : 'none';

    // Particles
    const particleCanvas = document.getElementById('particle-canvas');
    if (particleCanvas) particleCanvas.style.display = state.settings.particles ? 'block' : 'none';

    // Voice
    if (state.settings.voice && !state.voiceListening) toggleVoice();
    else if (!state.settings.voice && state.voiceListening) toggleVoice();
  }

  // ── Initialization ──
  function init() {
    initSettings();
    loadProfile();

    const btnSaveProfile = $('#btn-save-profile');
    if (btnSaveProfile) {
      btnSaveProfile.addEventListener('click', saveProfile);
    }

    // Clock
    updateClock();
    setInterval(updateClock, 1000);

    // Navigation
    $$('.nav-item').forEach((item) => {
      item.addEventListener('click', () => {
        const view = item.dataset.view;
        if (view) switchView(view);
      });
    });

    // Chat input
    const chatInput = $('#chat-input');
    const sendBtn = $('#btn-send');

    if (chatInput) {
      chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          const text = chatInput.value.trim();
          if (text) {
            sendCommand(text);
            chatInput.value = '';
          }
        }

        // History navigation
        if (e.key === 'ArrowUp' && state.commandHistory.length > 0) {
          e.preventDefault();
          state.historyIndex = Math.min(state.historyIndex + 1, state.commandHistory.length - 1);
          chatInput.value = state.commandHistory[state.historyIndex];
        }
        if (e.key === 'ArrowDown') {
          e.preventDefault();
          state.historyIndex = Math.max(state.historyIndex - 1, -1);
          chatInput.value = state.historyIndex >= 0 ? state.commandHistory[state.historyIndex] : '';
        }
      });

      // Auto-resize textarea
      chatInput.addEventListener('input', () => {
        chatInput.style.height = 'auto';
        chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
      });
    }

    if (sendBtn) {
      sendBtn.addEventListener('click', () => {
        const text = chatInput?.value.trim();
        if (text) {
          sendCommand(text);
          chatInput.value = '';
          chatInput.style.height = 'auto';
        }
      });
    }

    // Voice button
    const voiceBtn = $('.btn-voice');
    if (voiceBtn) {
      voiceBtn.addEventListener('click', toggleVoice);
    }
    
    // Save Profile button
    const btnSaveProfileElement = $('#btn-save-profile');
    if (btnSaveProfileElement) {
        btnSaveProfileElement.addEventListener('click', saveProfile);
    }

    // Particle System
    if (typeof ParticleSystem !== 'undefined') {
      state.particleSystem = new ParticleSystem('particle-canvas');
    }

    // WebSocket connection
    connectWebSocket();

    // Welcome message
    setTimeout(() => {
      addChatMessage('orpheus', 'ORPHEUS neural core initialized. All systems nominal. How can I assist you, Commander?');
      log('system', 'ORPHEUS v2.0 — Holographic Interface Active');
      addActivity({ icon: '🟢', text: 'System initialized', iconClass: '' });
    }, 800);

    // Initialize voice engine (preload voices)
    if (window.speechSynthesis) {
      window.speechSynthesis.getVoices();
    }
  }

  // ── Public API ──
  window.orpheus = {
    sendCommand,
    toggleVoice,
    switchView,
    readFile: (name) => {
      sendCommand(`read file ${name}`);
      switchView('chat');
    },
  };

  // ── Boot ──
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
