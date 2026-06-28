/* ============================================================
   ORPHEUS — Enhanced Neural Particle System
   Advanced Canvas-based "Mind Map / Neural Core" visualization
   ============================================================ */

class ParticleSystem {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    this.particles = [];
    this.signals = []; // Traveling data packets
    this.mouse = { x: null, y: null, radius: 150, clickPulse: 0, clickX: 0, clickY: 0 };
    this.state = 'idle'; // idle | thinking | active | error
    this.pulsePhase = 0;
    this.frameCount = 0;
    this.dpr = window.devicePixelRatio || 1;

    this._resize();
    this._initParticles();
    this._bindEvents();
    this._animate();
  }

  _resize() {
    const rect = this.canvas.parentElement.getBoundingClientRect();
    this.width = rect.width;
    this.height = rect.height;
    this.canvas.width = this.width * this.dpr;
    this.canvas.height = this.height * this.dpr;
    this.canvas.style.width = this.width + 'px';
    this.canvas.style.height = this.height + 'px';
    this.ctx.scale(this.dpr, this.dpr);
    this.centerX = this.width / 2;
    this.centerY = this.height / 2;
  }

  _initParticles() {
    this.particles = [];
    this.signals = [];
    
    // Create fewer particles for a lighter neural net
    const count = Math.min(80, Math.floor((this.width * this.height) / 4000));

    for (let i = 0; i < count; i++) {
      const angle = Math.random() * Math.PI * 2;
      // Distribution: dense in center, sparse at edges
      const distPercent = Math.pow(Math.random(), 1.5); 
      const radius = distPercent * Math.min(this.width, this.height) * 0.45;
      
      const x = this.centerX + Math.cos(angle) * radius;
      const y = this.centerY + Math.sin(angle) * radius;
      
      // Determine node type based on distance from center
      let type = 'axon'; // default outer
      if (distPercent < 0.2) type = 'core';
      else if (distPercent < 0.6) type = 'synapse';

      this.particles.push({
        id: i,
        x, y,
        baseX: x,
        baseY: y,
        vx: (Math.random() - 0.5) * 0.5,
        vy: (Math.random() - 0.5) * 0.5,
        size: type === 'core' ? Math.random() * 3 + 2 : (type === 'synapse' ? Math.random() * 2 + 1.5 : Math.random() * 1.5 + 0.5),
        opacity: type === 'core' ? 0.9 : (type === 'synapse' ? 0.6 : 0.3),
        hue: Math.random() > 0.6 ? 185 : 260, // cyan or purple dominance
        pulseOffset: Math.random() * Math.PI * 2,
        type: type,
        connections: [] // cache nearby nodes
      });
    }
  }

  _bindEvents() {
    window.addEventListener('resize', () => {
      this._resize();
      this._initParticles();
    });

    this.canvas.addEventListener('mousemove', (e) => {
      const rect = this.canvas.getBoundingClientRect();
      this.mouse.x = e.clientX - rect.left;
      this.mouse.y = e.clientY - rect.top;
    });

    this.canvas.addEventListener('mouseleave', () => {
      this.mouse.x = null;
      this.mouse.y = null;
    });
    
    this.canvas.addEventListener('click', (e) => {
      const rect = this.canvas.getBoundingClientRect();
      this.mouse.clickX = e.clientX - rect.left;
      this.mouse.clickY = e.clientY - rect.top;
      this.mouse.clickPulse = 1; // trigger click shockwave
      
      // Spawn some signals
      for(let i=0; i<5; i++) {
         this._spawnSignal(this.particles[Math.floor(Math.random() * this.particles.length)]);
      }
    });
  }

  setState(state) {
    this.state = state;
  }

  pulse() {
    this.pulsePhase = 1;
    // Spawn signals on pulse
    const coreNodes = this.particles.filter(p => p.type === 'core');
    for(let i=0; i<8; i++) {
       if(coreNodes.length) this._spawnSignal(coreNodes[Math.floor(Math.random() * coreNodes.length)]);
    }
  }
  
  _spawnSignal(startNode) {
    if(!startNode) return;
    this.signals.push({
      x: startNode.x,
      y: startNode.y,
      currentNode: startNode,
      targetNode: null,
      progress: 0,
      speed: Math.random() * 0.02 + 0.02,
      life: 1.0
    });
  }

  _animate() {
    this.frameCount++;
    this.ctx.clearRect(0, 0, this.width, this.height);

    // Update global pulse
    if (this.pulsePhase > 0) this.pulsePhase -= 0.015;
    
    // Update click pulse
    if (this.mouse.clickPulse > 0) this.mouse.clickPulse -= 0.02;

    // State Colors & Properties
    let primaryHue = 185;   // Cyan
    let secondaryHue = 260; // Purple
    let speedMult = 1;
    let glowIntensity = 0.4;

    switch (this.state) {
      case 'thinking':
        speedMult = 2.5;
        glowIntensity = 0.7;
        break;
      case 'active':
        speedMult = 1.8;
        glowIntensity = 0.6;
        primaryHue = 155; // Green-cyan
        break;
      case 'error':
        primaryHue = 0;   // Red
        secondaryHue = 30; // Orange
        glowIntensity = 0.8;
        speedMult = 3;
        break;
    }
    
    const isLight = document.body.classList.contains('light-theme');
    
    // In light theme, change to a different, friendly color scheme (e.g. Blue & Pinkish Orange)
    if (isLight) {
        if (this.state === 'idle') {
            primaryHue = 210;    // Deep Blue
            secondaryHue = 330;  // Magenta/Pink
        } else if (this.state === 'active') {
            primaryHue = 200;    // Light Blue
            secondaryHue = 40;   // Orange
        }
    }

    const lBase = isLight ? 40 : 60;
    const lDark = isLight ? 30 : 50;
    const lBright = isLight ? 45 : 70;
    const lCore = isLight ? 50 : 80;

    // --- 1. Draw Background Core Glow ---
    const coreGlow = this.ctx.createRadialGradient(
      this.centerX, this.centerY, 0,
      this.centerX, this.centerY, Math.min(this.width, this.height) * 0.4
    );
    const breathe = Math.sin(this.frameCount * 0.02) * 0.5 + 0.5;
    const coreOpacity = (0.02 + breathe * 0.05 + this.pulsePhase * 0.1) * (glowIntensity / 0.4);
    
    coreGlow.addColorStop(0, `hsla(${primaryHue}, 100%, ${lBase}%, ${coreOpacity})`);
    coreGlow.addColorStop(0.4, `hsla(${secondaryHue}, 80%, ${lDark}%, ${coreOpacity * 0.4})`);
    coreGlow.addColorStop(1, 'transparent');
    this.ctx.fillStyle = coreGlow;
    this.ctx.fillRect(0, 0, this.width, this.height);

    // --- 2. Update Particles ---
    this.particles.forEach((p) => {
      // Natural drifting motion
      const time = this.frameCount * 0.005 * speedMult;
      
      // Floating offset
      const floatX = Math.sin(time + p.pulseOffset) * 15;
      const floatY = Math.cos(time * 0.8 + p.pulseOffset) * 15;
      
      // Target position
      let targetX = p.baseX + floatX;
      let targetY = p.baseY + floatY;

      // Mouse Interactions (Repel/Parallax)
      if (this.mouse.x !== null) {
        const dx = this.mouse.x - targetX;
        const dy = this.mouse.y - targetY;
        const dist = Math.sqrt(dx * dx + dy * dy);
        
        if (dist < this.mouse.radius) {
          const force = (this.mouse.radius - dist) / this.mouse.radius;
          // Repel slightly
          targetX -= dx * force * 0.2;
          targetY -= dy * force * 0.2;
        }
      }
      
      // Click Shockwave
      if (this.mouse.clickPulse > 0) {
        const dx = targetX - this.mouse.clickX;
        const dy = targetY - this.mouse.clickY;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const waveRadius = (1 - this.mouse.clickPulse) * Math.max(this.width, this.height);
        
        // If particle is near the expanding wave boundary
        if (Math.abs(dist - waveRadius) < 50) {
            const pushForce = Math.sin(this.mouse.clickPulse * Math.PI) * 20;
            const angle = Math.atan2(dy, dx);
            targetX += Math.cos(angle) * pushForce;
            targetY += Math.sin(angle) * pushForce;
        }
      }

      // Smooth follow target
      p.x += (targetX - p.x) * 0.1;
      p.y += (targetY - p.y) * 0.1;

      // Random signal generation based on state
      if (Math.random() < 0.001 * speedMult) {
        this._spawnSignal(p);
      }
    });

    // --- 3. Update & Draw Connections (Network Topology) ---
    // Recalculate connections occasionally for performance
    if (this.frameCount % 20 === 0) {
      this.particles.forEach(p => p.connections = []);
      const maxDist = 100;
      for (let i = 0; i < this.particles.length; i++) {
        for (let j = i + 1; j < this.particles.length; j++) {
          const dx = this.particles[i].x - this.particles[j].x;
          const dy = this.particles[i].y - this.particles[j].y;
          const distSq = dx*dx + dy*dy;
          if (distSq < maxDist * maxDist) {
            this.particles[i].connections.push(this.particles[j]);
            this.particles[j].connections.push(this.particles[i]);
          }
        }
      }
    }

    this.ctx.lineWidth = 0.8;
    for (let i = 0; i < this.particles.length; i++) {
      const p1 = this.particles[i];
      for (let j = 0; j < p1.connections.length; j++) {
        const p2 = p1.connections[j];
        if (p1.id > p2.id) continue; // draw once
        
        const dx = p1.x - p2.x;
        const dy = p1.y - p2.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const opacity = (1 - (dist / 110)) * 0.25 * (glowIntensity / 0.4);
        
        this.ctx.beginPath();
        this.ctx.moveTo(p1.x, p1.y);
        this.ctx.lineTo(p2.x, p2.y);
        
        // Simplified solid color connection for performance
        const p1Hue = p1.hue === 185 ? primaryHue : secondaryHue;
        this.ctx.strokeStyle = `hsla(${p1Hue}, 80%, ${lBase}%, ${opacity})`;
        this.ctx.stroke();
      }
    }

    // --- 4. Update & Draw Traveling Signals (Data Packets) ---
    for (let i = this.signals.length - 1; i >= 0; i--) {
        const sig = this.signals[i];
        
        if (!sig.targetNode) {
            // Pick a random connected node
            if (sig.currentNode.connections.length > 0) {
                sig.targetNode = sig.currentNode.connections[Math.floor(Math.random() * sig.currentNode.connections.length)];
            } else {
                this.signals.splice(i, 1);
                continue;
            }
        }
        
        sig.progress += sig.speed * speedMult;
        
        if (sig.progress >= 1) {
            // Arrived at target, jump to next
            sig.currentNode = sig.targetNode;
            sig.targetNode = null;
            sig.progress = 0;
            sig.life -= 0.1; // Degrade over hops
            
            // Pulse the node it hits
            const hitHue = sig.currentNode.hue === 185 ? primaryHue : secondaryHue;
            this.ctx.beginPath();
            this.ctx.arc(sig.currentNode.x, sig.currentNode.y, sig.currentNode.size * 4, 0, Math.PI * 2);
            this.ctx.fillStyle = `hsla(${hitHue}, 100%, ${lBright}%, ${sig.life * 0.5})`;
            this.ctx.fill();
        } else {
            // Lerp position
            sig.x = sig.currentNode.x + (sig.targetNode.x - sig.currentNode.x) * sig.progress;
            sig.y = sig.currentNode.y + (sig.targetNode.y - sig.currentNode.y) * sig.progress;
            
            // Draw signal blip
            const sigHue = sig.currentNode.hue === 185 ? primaryHue : secondaryHue;
            this.ctx.beginPath();
            this.ctx.arc(sig.x, sig.y, 2, 0, Math.PI * 2);
            this.ctx.fillStyle = `hsla(${sigHue}, 100%, ${lCore}%, ${sig.life})`;
            this.ctx.shadowBlur = 10;
            this.ctx.shadowColor = `hsl(${sigHue}, 100%, ${lDark}%)`;
            this.ctx.fill();
            this.ctx.shadowBlur = 0; // reset
        }
        
        if (sig.life <= 0) {
            this.signals.splice(i, 1);
        }
    }

    // --- 5. Draw Particles (Nodes) ---
    this.particles.forEach((p) => {
      const pulseFactor = this.pulsePhase > 0 ? Math.sin(this.pulsePhase * Math.PI) * 0.5 : 0;
      const particleHue = p.hue === 185 ? primaryHue : secondaryHue;
      const particleOpacity = p.opacity + breathe * 0.1 + pulseFactor;
      const particleSize = p.size * (1 + pulseFactor * 0.5);

      // Outer glow
      this.ctx.beginPath();
      this.ctx.arc(p.x, p.y, particleSize * 4, 0, Math.PI * 2);
      this.ctx.fillStyle = `hsla(${particleHue}, 100%, ${lBase}%, ${particleOpacity * 0.15})`;
      this.ctx.fill();

      // Core
      this.ctx.beginPath();
      this.ctx.arc(p.x, p.y, particleSize, 0, Math.PI * 2);
      this.ctx.fillStyle = `hsla(${particleHue}, 100%, ${lCore}%, ${particleOpacity})`;
      this.ctx.fill();
    });

    // --- 6. Draw System Pulse Rings ---
    if (this.pulsePhase > 0) {
      const ringRadius = (1 - this.pulsePhase) * Math.max(this.width, this.height) * 0.5;
      this.ctx.beginPath();
      this.ctx.arc(this.centerX, this.centerY, ringRadius, 0, Math.PI * 2);
      this.ctx.strokeStyle = `hsla(${primaryHue}, 100%, ${lBase}%, ${this.pulsePhase * 0.4})`;
      this.ctx.lineWidth = 3;
      this.ctx.stroke();
    }
    
    // Draw click pulse ring
    if (this.mouse.clickPulse > 0) {
      const waveRadius = (1 - this.mouse.clickPulse) * Math.max(this.width, this.height);
      this.ctx.beginPath();
      this.ctx.arc(this.mouse.clickX, this.mouse.clickY, waveRadius, 0, Math.PI * 2);
      this.ctx.strokeStyle = `hsla(${secondaryHue}, 100%, ${lBright}%, ${this.mouse.clickPulse * 0.5})`;
      this.ctx.lineWidth = 2;
      this.ctx.stroke();
    }

    requestAnimationFrame(() => this._animate());
  }
}

// Export for use in app.js
window.ParticleSystem = ParticleSystem;
