// ============================================================
// ORPHEUS — Landing Page 3D Scene
// Space theme with nebulas, stars, and glossy 3D core
// ============================================================

(function() {
    // Basic Scene Setup
    const container = document.getElementById('canvas-container');
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x030712, 0.0015);

    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.z = 30;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;
    container.appendChild(renderer.domElement);

    // ============================================================
    // 1. OUTER SPACE (STARS & NEBULA)
    // ============================================================

    // Stars Particle System
    const starGeometry = new THREE.BufferGeometry();
    const starCount = 3000;
    const starPos = new Float32Array(starCount * 3);
    const starColors = new Float32Array(starCount * 3);

    const color1 = new THREE.Color(0x00F0FF); // Cyan
    const color2 = new THREE.Color(0x8B5CF6); // Purple
    const color3 = new THREE.Color(0xFFFFFF); // White

    for(let i = 0; i < starCount * 3; i+=3) {
        // Spherical distribution
        const r = 40 + Math.random() * 200;
        const theta = 2 * Math.PI * Math.random();
        const phi = Math.acos(2 * Math.random() - 1);

        starPos[i] = r * Math.sin(phi) * Math.cos(theta);
        starPos[i+1] = r * Math.sin(phi) * Math.sin(theta);
        starPos[i+2] = r * Math.cos(phi);

        // Mix colors
        const randColor = Math.random();
        let mixColor = color3;
        if(randColor > 0.8) mixColor = color1;
        else if(randColor > 0.6) mixColor = color2;

        starColors[i] = mixColor.r;
        starColors[i+1] = mixColor.g;
        starColors[i+2] = mixColor.b;
    }

    starGeometry.setAttribute('position', new THREE.BufferAttribute(starPos, 3));
    starGeometry.setAttribute('color', new THREE.BufferAttribute(starColors, 3));

    const starMaterial = new THREE.PointsMaterial({
        size: 0.15,
        vertexColors: true,
        transparent: true,
        opacity: 0.8,
        sizeAttenuation: true
    });

    const stars = new THREE.Points(starGeometry, starMaterial);
    scene.add(stars);

    // ============================================================
    // 2. THE GLOSSY 3D OBJECT (NEURAL CORE)
    // ============================================================

    // Complex Torus Knot
    const coreGeometry = new THREE.TorusKnotGeometry(8, 2.5, 200, 32, 3, 4);
    
    // Premium Glossy Material
    const coreMaterial = new THREE.MeshPhysicalMaterial({
        color: 0x111111,
        metalness: 0.9,
        roughness: 0.1,
        transmission: 0.6, // Glass-like
        thickness: 0.5,
        ior: 1.5,
        envMapIntensity: 1.0,
        clearcoat: 1.0,
        clearcoatRoughness: 0.1,
        wireframe: false
    });

    const coreMesh = new THREE.Mesh(coreGeometry, coreMaterial);
    
    // Position object slightly to the right on desktop, center on mobile
    if (window.innerWidth > 768) {
        coreMesh.position.x = 12;
    }
    
    scene.add(coreMesh);

    // Inner glowing sphere
    const innerGeo = new THREE.IcosahedronGeometry(4, 2);
    const innerMat = new THREE.MeshBasicMaterial({
        color: 0x00F0FF,
        wireframe: true,
        transparent: true,
        opacity: 0.15
    });
    const innerMesh = new THREE.Mesh(innerGeo, innerMat);
    coreMesh.add(innerMesh);

    // ============================================================
    // 3. LIGHTING (NEBULA GLOW)
    // ============================================================

    const ambientLight = new THREE.AmbientLight(0x111111);
    scene.add(ambientLight);

    // Cyan Light
    const light1 = new THREE.PointLight(0x00F0FF, 5, 100);
    light1.position.set(20, 20, 20);
    scene.add(light1);

    // Purple Light
    const light2 = new THREE.PointLight(0x8B5CF6, 5, 100);
    light2.position.set(-20, -20, 20);
    scene.add(light2);

    // Backlight
    const light3 = new THREE.PointLight(0xEC4899, 2, 100);
    light3.position.set(0, 0, -30);
    scene.add(light3);

    // ============================================================
    // 4. INTERACTION & ANIMATION
    // ============================================================

    let mouseX = 0;
    let mouseY = 0;
    let targetX = 0;
    let targetY = 0;

    const windowHalfX = window.innerWidth / 2;
    const windowHalfY = window.innerHeight / 2;

    document.addEventListener('mousemove', (event) => {
        mouseX = (event.clientX - windowHalfX) * 0.001;
        mouseY = (event.clientY - windowHalfY) * 0.001;
    });

    // Resize Handler
    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
        
        if (window.innerWidth > 768) {
            coreMesh.position.x = 12;
        } else {
            coreMesh.position.x = 0;
        }
    });

    const clock = new THREE.Clock();

    function animate() {
        requestAnimationFrame(animate);

        const elapsedTime = clock.getElapsedTime();

        // Smooth mouse follow for camera
        targetX = mouseX * 2;
        targetY = mouseY * 2;
        camera.position.x += (targetX - camera.position.x) * 0.02;
        camera.position.y += (-targetY - camera.position.y) * 0.02;
        camera.lookAt(scene.position);

        // Rotate Object
        coreMesh.rotation.x = elapsedTime * 0.1;
        coreMesh.rotation.y = elapsedTime * 0.15;
        
        // Inner mesh spins opposite
        innerMesh.rotation.x = -elapsedTime * 0.2;
        innerMesh.rotation.y = -elapsedTime * 0.1;

        // Rotate Stars slowly
        stars.rotation.y = elapsedTime * 0.02;

        // Dynamic Nebula Lighting
        light1.position.x = Math.sin(elapsedTime * 0.5) * 30;
        light1.position.z = Math.cos(elapsedTime * 0.5) * 30;
        
        light2.position.y = Math.sin(elapsedTime * 0.3) * 30;
        light2.position.z = Math.cos(elapsedTime * 0.3) * 30;

        renderer.render(scene, camera);
    }

    animate();
})();

// ============================================================
// LOGIN AUTHENTICATION LOGIC
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const guestBtn = document.getElementById('guest-btn');
    const submitBtn = document.getElementById('submit-btn');
    const btnText = document.querySelector('.btn-text');
    const loader = document.getElementById('loader');
    const errorMessage = document.getElementById('error-message');

    function setLoading(isLoading) {
        if(isLoading) {
            submitBtn.disabled = true;
            btnText.style.display = 'none';
            loader.style.display = 'inline-block';
            guestBtn.disabled = true;
        } else {
            submitBtn.disabled = false;
            btnText.style.display = 'inline-block';
            loader.style.display = 'none';
            guestBtn.disabled = false;
        }
    }

    function showError(msg) {
        errorMessage.textContent = msg;
        setTimeout(() => errorMessage.textContent = '', 5000);
    }

    // Email Login
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('email').value;
        
        setLoading(true);
        errorMessage.textContent = '';

        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: email })
            });

            if(response.ok) {
                // Success! Redirect to app
                window.location.href = '/app';
            } else if (response.status === 429) {
                showError("RATE LIMIT EXCEEDED: MAXIMUM ATTEMPTS REACHED. PLEASE WAIT 15 MINUTES.");
            } else {
                const data = await response.json();
                showError(data.message || 'Authentication failed. Neural link rejected.');
            }
        } catch (err) {
            showError('Network error. Unable to establish connection to ORPHEUS core.');
        } finally {
            setLoading(false);
        }
    });

    // Guest Login
    guestBtn.addEventListener('click', async () => {
        setLoading(true);
        errorMessage.textContent = '';

        try {
            const response = await fetch('/api/guest_login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if(response.ok) {
                // Success! Redirect to app
                window.location.href = '/app';
            } else if (response.status === 429) {
                showError("RATE LIMIT EXCEEDED: MAXIMUM ATTEMPTS REACHED. PLEASE WAIT 15 MINUTES.");
            } else {
                showError('Guest access denied.');
            }
        } catch (err) {
            showError('Network error. Unable to establish connection to ORPHEUS core.');
        } finally {
            setLoading(false);
        }
    });
});
