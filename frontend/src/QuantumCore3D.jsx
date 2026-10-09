import React, { useEffect, useRef } from "react";
import * as THREE from "three";

export default function QuantumCore3D() {
  const mountRef = useRef(null);

  useEffect(() => {
    const currentMount = mountRef.current;
    if (!currentMount) return;

    const width = currentMount.clientWidth || 400;
    const height = currentMount.clientHeight || 300;

    // Scene, Camera, Renderer
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.z = 7;

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    currentMount.appendChild(renderer.domElement);

    // 1. Quantum Core Sphere (Icosphere + Wireframe)
    const sphereGeo = new THREE.IcosahedronGeometry(1.6, 2);
    const sphereMat = new THREE.MeshPhongMaterial({
      color: 0x8B5CF6,
      emissive: 0x4C1D95,
      wireframe: true,
      transparent: true,
      opacity: 0.8
    });
    const coreSphere = new THREE.Mesh(sphereGeo, sphereMat);
    scene.add(coreSphere);

    // Inner Glowing Core
    const innerGeo = new THREE.SphereGeometry(1.1, 32, 32);
    const innerMat = new THREE.MeshBasicMaterial({
      color: 0x06B6D4,
      wireframe: false,
      transparent: true,
      opacity: 0.4
    });
    const innerCore = new THREE.Mesh(innerGeo, innerMat);
    scene.add(innerCore);

    // 2. Orbital Rings
    const ring1Geo = new THREE.TorusGeometry(2.4, 0.02, 16, 100);
    const ring1Mat = new THREE.MeshBasicMaterial({ color: 0x06B6D4 });
    const ring1 = new THREE.Mesh(ring1Geo, ring1Mat);
    ring1.rotation.x = Math.PI / 3;
    scene.add(ring1);

    const ring2Geo = new THREE.TorusGeometry(2.8, 0.02, 16, 100);
    const ring2Mat = new THREE.MeshBasicMaterial({ color: 0xEC4899 });
    const ring2 = new THREE.Mesh(ring2Geo, ring2Mat);
    ring2.rotation.y = Math.PI / 4;
    scene.add(ring2);

    // 3. Transaction Particle Swarm
    const particleCount = 400;
    const particlesGeo = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);

    const colorNormal = new THREE.Color(0x10B981);
    const colorFraud = new THREE.Color(0xEF4444);

    for (let i = 0; i < particleCount; i++) {
      const radius = 3.2 + Math.random() * 1.5;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(Math.random() * 2 - 1);

      positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
      positions[i * 3 + 2] = radius * Math.cos(phi);

      const isFraud = Math.random() < 0.08;
      const c = isFraud ? colorFraud : colorNormal;
      colors[i * 3] = c.r;
      colors[i * 3 + 1] = c.g;
      colors[i * 3 + 2] = c.b;
    }

    particlesGeo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    particlesGeo.setAttribute("color", new THREE.BufferAttribute(colors, 3));

    const particlesMat = new THREE.PointsMaterial({
      size: 0.08,
      vertexColors: true,
      transparent: true,
      opacity: 0.85
    });

    const particleSystem = new THREE.Points(particlesGeo, particlesMat);
    scene.add(particleSystem);

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
    scene.add(ambientLight);

    const pointLight = new THREE.PointLight(0x06B6D4, 2, 50);
    pointLight.position.set(5, 5, 5);
    scene.add(pointLight);

    // Mouse interactivity
    let mouseX = 0, mouseY = 0;
    const handleMouseMove = (e) => {
      mouseX = (e.clientX / window.innerWidth) * 2 - 1;
      mouseY = -(e.clientY / window.innerHeight) * 2 + 1;
    };
    window.addEventListener("mousemove", handleMouseMove);

    // Animation Loop
    let animationFrameId;
    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);

      coreSphere.rotation.x += 0.004;
      coreSphere.rotation.y += 0.006;

      innerCore.rotation.y -= 0.008;

      ring1.rotation.z += 0.01;
      ring2.rotation.z -= 0.008;

      particleSystem.rotation.y += 0.003;

      // Camera parallax following mouse
      camera.position.x += (mouseX * 1.5 - camera.position.x) * 0.05;
      camera.position.y += (mouseY * 1.5 - camera.position.y) * 0.05;
      camera.lookAt(scene.position);

      renderer.render(scene, camera);
    };
    animate();

    // Handle Resize
    const handleResize = () => {
      if (!currentMount) return;
      const w = currentMount.clientWidth;
      const h = currentMount.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("resize", handleResize);
      cancelAnimationFrame(animationFrameId);
      if (currentMount.contains(renderer.domElement)) {
        currentMount.removeChild(renderer.domElement);
      }
    };
  }, []);

  return <div ref={mountRef} className="canvas-3d-wrapper" style={{ width: "100%", height: "340px", position: "relative" }} />;
}
