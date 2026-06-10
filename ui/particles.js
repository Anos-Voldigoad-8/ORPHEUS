/* ============================================================
   ORPHEUS — Neural Particle System
   Canvas-based "AI Brain" visualization
   ============================================================ */

class ParticleSystem {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    this.particles = [];
    this.connections = [];
    this.mouse = { x: null, y: null, radius: 120 };
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
    const count = Math.min(80, Math.floor((this.width * this.height) / 4000));

    for (let i = 0; i < count; i++) {
      // Cluster particles around center with some scatter
      const angle = Math.random() * Math.PI * 2;
      const radius = Math.random() * Math.min(this.width, this.height) * 0.38;
      const x = this.centerX + Math.cos(angle) * radius;
      const y = this.centerY + Math.sin(angle) * radius;

      this.particles.push({
        x, y,
        originX: x,
        originY: y,
        vx: (Math.random() - 0.5) * 0.3,
        vy: (Math.random() - 0.5) * 0.3,
        size: Math.random() * 2.5 + 1,
        opacity: Math.random() * 0.5 + 0.3,
        hue: Math.random() > 0.5 ? 185 : 260, // cyan or purple
        pulseOffset: Math.random() * Math.PI * 2,
        layer: Math.floor(Math.random() * 3), // 0=close, 1=mid, 2=far
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
  }

  setState(state) {
    this.state = state;
  }

  pulse() {
    // Trigger a single pulse effect
    this.pulsePhase = 1;
  }

  _animate() {
    this.frameCount++;
    this.ctx.clearRect(0, 0, this.width, this.height);

    // Update pulse
    if (this.pulsePhase > 0) {
      this.pulsePhase -= 0.015;
    }

    // State-based colors
    let primaryHue = 185;   // cyan
    let secondaryHue = 260; // purple
    let speed = 1;
    let glowIntensity = 0.3;

    switch (this.state) {
      case 'thinking':
        speed = 2.5;
        glowIntensity = 0.6;
        break;
      case 'active':
        speed = 1.5;
        glowIntensity = 0.5;
        primaryHue = 155; // green-cyan
        break;
      case 'error':
        primaryHue = 0;
        secondaryHue = 30;
        glowIntensity = 0.7;
        speed = 3;
        break;
    }

    // Draw center glow
    const coreGlow = this.ctx.createRadialGradient(
      this.centerX, this.centerY, 0,
      this.centerX, this.centerY, Math.min(this.width, this.height) * 0.3
    );

    const breathe = Math.sin(this.frameCount * 0.02) * 0.5 + 0.5;
    const coreOpacity = (0.03 + breathe * 0.04 + this.pulsePhase * 0.08) * (glowIntensity / 0.3);

    coreGlow.addColorStop(0, `hsla(${primaryHue}, 100%, 60%, ${coreOpacity})`);
    coreGlow.addColorStop(0.5, `hsla(${secondaryHue}, 80%, 50%, ${coreOpacity * 0.3})`);
    coreGlow.addColorStop(1, 'transparent');
    this.ctx.fillStyle = coreGlow;
    this.ctx.fillRect(0, 0, this.width, this.height);

    // Update and draw particles
    this.particles.forEach((p, i) => {
      // Movement
      const time = this.frameCount * 0.01 * speed;
      const orbitSpeed = 0.001 * (p.layer + 1) * speed;

      // Gentle orbital motion
      p.x = p.originX + Math.sin(time + p.pulseOffset) * (8 + p.layer * 4);
      p.y = p.originY + Math.cos(time * 0.7 + p.pulseOffset) * (6 + p.layer * 3);

      // Mouse interaction
      if (this.mouse.x !== null) {
        const dx = this.mouse.x - p.x;
        const dy = this.mouse.y - p.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < this.mouse.radius) {
          const force = (this.mouse.radius - dist) / this.mouse.radius;
          p.x -= dx * force * 0.03;
          p.y -= dy * force * 0.03;
        }
      }

      // Pulse effect
      const pulseFactor = this.pulsePhase > 0 ?
        Math.sin(this.pulsePhase * Math.PI) * 0.5 : 0;

      // Draw particle
      const particleHue = p.hue === 185 ? primaryHue : secondaryHue;
      const particleOpacity = p.opacity + breathe * 0.2 + pulseFactor;
      const particleSize = p.size * (1 + pulseFactor * 0.5);

      // Outer glow
      this.ctx.beginPath();
      this.ctx.arc(p.x, p.y, particleSize * 3, 0, Math.PI * 2);
      this.ctx.fillStyle = `hsla(${particleHue}, 100%, 60%, ${particleOpacity * 0.1})`;
      this.ctx.fill();

      // Core
      this.ctx.beginPath();
      this.ctx.arc(p.x, p.y, particleSize, 0, Math.PI * 2);
      this.ctx.fillStyle = `hsla(${particleHue}, 100%, 70%, ${particleOpacity})`;
      this.ctx.fill();
    });

    // Draw connections
    const maxDist = 80;
    for (let i = 0; i < this.particles.length; i++) {
      for (let j = i + 1; j < this.particles.length; j++) {
        const dx = this.particles[i].x - this.particles[j].x;
        const dy = this.particles[i].y - this.particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < maxDist) {
          const opacity = (1 - dist / maxDist) * 0.15 * (glowIntensity / 0.3);
          this.ctx.beginPath();
          this.ctx.moveTo(this.particles[i].x, this.particles[i].y);
          this.ctx.lineTo(this.particles[j].x, this.particles[j].y);
          this.ctx.strokeStyle = `hsla(${primaryHue}, 80%, 60%, ${opacity})`;
          this.ctx.lineWidth = 0.5;
          this.ctx.stroke();
        }
      }
    }

    // Draw pulse ring
    if (this.pulsePhase > 0) {
      const ringRadius = (1 - this.pulsePhase) * Math.min(this.width, this.height) * 0.4;
      this.ctx.beginPath();
      this.ctx.arc(this.centerX, this.centerY, ringRadius, 0, Math.PI * 2);
      this.ctx.strokeStyle = `hsla(${primaryHue}, 100%, 60%, ${this.pulsePhase * 0.3})`;
      this.ctx.lineWidth = 2;
      this.ctx.stroke();
    }

    requestAnimationFrame(() => this._animate());
  }
}

// Export for use in app.js
window.ParticleSystem = ParticleSystem;
