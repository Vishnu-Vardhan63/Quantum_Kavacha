import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";

// Helper to determine color from node type and risk
function getNodeColor(node) {
  if (node.is_case_anchor) return 0xFF0055; // Vibrant neon magenta/red for anchor
  if (node.type === "MULE_HUB") return 0x8B5CF6; // Violet
  if (node.type === "NETWORK_DOMAIN") return node.risk_score > 70 ? 0xEF4444 : 0x06B6D4;
  if (node.type === "RECIPIENT") return node.risk_score > 70 ? 0xEF4444 : 0x10B981;
  if (node.type === "DEVICE") return node.risk_score > 70 ? 0xF59E0B : 0x06B6D4;
  if (node.type === "USER") return node.risk_score > 70 ? 0xF87171 : 0x10B981;
  if (node.type === "IP") return 0x06B6D4;
  
  if (node.risk_score >= 80) return 0xEF4444;
  if (node.risk_score >= 50) return 0xF59E0B;
  return 0x10B981;
}

function getNodeSize(node) {
  if (node.is_case_anchor) return 0.65;
  if (node.type === "MULE_HUB") return 0.55;
  if (node.type === "TRANSACTION") return 0.5;
  return 0.4;
}

export default function TransactionGraph3D({ graphData, onSelectNode, selectedNodeId }) {
  const mountRef = useRef(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [autoRotate, setAutoRotate] = useState(false); // Default false for performance

  const sceneRef = useRef(null);
  const cameraRef = useRef(null);
  const controlsRef = useRef(null);
  const nodeMeshesRef = useRef([]);

  // If graphData has no nodes, return clean fallback without fabricating entities
  if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
    return (
      <div style={{ width: "100%", height: "420px", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", background: "rgba(15, 23, 42, 0.6)", borderRadius: "12px", border: "1px dashed rgba(255, 255, 255, 0.1)", color: "#94A3B8", textAlign: "center", padding: "2rem" }}>
        <div style={{ width: "48px", height: "48px", borderRadius: "50%", background: "rgba(100, 116, 139, 0.15)", display: "flex", alignItems: "center", justifyContent: "center", marginBottom: "0.8rem" }}>
          ⚛
        </div>
        <h4 style={{ color: "#F8FAFC", fontSize: "0.95rem", margin: "0 0 0.3rem 0" }}>GRAPH DATA UNAVAILABLE</h4>
        <p style={{ fontSize: "0.82rem", maxWidth: "380px", margin: 0, color: "#94A3B8" }}>
          Relationships could not be established from the available case evidence.
        </p>
      </div>
    );
  }

  const activeData = graphData;


  useEffect(() => {
    const currentMount = mountRef.current;
    if (!currentMount) return;

    const width = currentMount.clientWidth || 700;
    const height = currentMount.clientHeight || 420;

    // 1. Scene & Camera
    const scene = new THREE.Scene();
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(0, 2, 14);
    cameraRef.current = camera;

    // 2. WebGL Renderer
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;
    currentMount.appendChild(renderer.domElement);

    // 3. Orbit Controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.maxDistance = 30;
    controls.minDistance = 3;
    controlsRef.current = controls;

    // 4. Lighting & Ambient
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
    scene.add(ambientLight);

    const keyLight = new THREE.PointLight(0x06B6D4, 3, 50);
    keyLight.position.set(6, 8, 8);
    scene.add(keyLight);

    const fillLight = new THREE.PointLight(0x8B5CF6, 2, 50);
    fillLight.position.set(-8, -6, 6);
    scene.add(fillLight);

    // Starfield particles background
    const starCount = 300;
    const starGeo = new THREE.BufferGeometry();
    const starPositions = new Float32Array(starCount * 3);
    for (let i = 0; i < starCount * 3; i += 3) {
      starPositions[i] = (Math.random() - 0.5) * 40;
      starPositions[i + 1] = (Math.random() - 0.5) * 40;
      starPositions[i + 2] = (Math.random() - 0.5) * 40;
    }
    starGeo.setAttribute("position", new THREE.BufferAttribute(starPositions, 3));
    const starMat = new THREE.PointsMaterial({ color: 0x334155, size: 0.1, transparent: true, opacity: 0.4 });
    const stars = new THREE.Points(starGeo, starMat);
    scene.add(stars);

    // 5. Build Node Meshes
    const nodeMap = new Map();
    const nodeMeshes = [];

    activeData.nodes.forEach((n, idx) => {
      const radius = getNodeSize(n);
      const color = getNodeColor(n);
      const sphereGeo = new THREE.SphereGeometry(radius, 24, 24);
      
      const mat = new THREE.MeshPhongMaterial({
        color: color,
        emissive: color,
        emissiveIntensity: n.is_case_anchor ? 0.7 : 0.4,
        shininess: 90,
        wireframe: false
      });

      const mesh = new THREE.Mesh(sphereGeo, mat);
      
      // Calculate position
      let p = n.pos_3d;
      if (!p || p.length < 3) {
        const phi = (idx / activeData.nodes.length) * Math.PI * 2;
        const dist = n.is_case_anchor ? 0 : 3.5;
        p = [Math.cos(phi) * dist, Math.sin(phi) * dist, (Math.random() - 0.5) * 2];
      }
      mesh.position.set(p[0], p[1], p[2]);
      mesh.userData = n;
      scene.add(mesh);
      nodeMeshes.push(mesh);
      nodeMap.set(n.id, mesh);

      // Glowing Aura Ring for High Risk and Anchor nodes
      if (n.is_case_anchor || n.risk_score >= 80) {
        const ringGeo = new THREE.RingGeometry(radius * 1.3, radius * 1.55, 32);
        const ringMat = new THREE.MeshBasicMaterial({
          color: color,
          side: THREE.DoubleSide,
          transparent: true,
          opacity: 0.6
        });
        const ringMesh = new THREE.Mesh(ringGeo, ringMat);
        ringMesh.position.set(p[0], p[1], p[2]);
        mesh.add(ringMesh);
      }
    });

    nodeMeshesRef.current = nodeMeshes;

    // 6. Build Edge Lines
    const lineMat = new THREE.LineBasicMaterial({
      color: 0x8B5CF6,
      transparent: true,
      opacity: 0.45,
      linewidth: 1.5
    });

    const highRiskLineMat = new THREE.LineBasicMaterial({
      color: 0xEF4444,
      transparent: true,
      opacity: 0.75,
      linewidth: 2.0
    });

    activeData.edges.forEach((edge) => {
      const srcMesh = nodeMap.get(edge.source);
      const tgtMesh = nodeMap.get(edge.target);
      if (srcMesh && tgtMesh) {
        const points = [srcMesh.position.clone(), tgtMesh.position.clone()];
        const lineGeo = new THREE.BufferGeometry().setFromPoints(points);
        const isHigh = edge.risk_weight >= 0.85 || edge.relationship === "MULE_TRANSFER";
        const line = new THREE.Line(lineGeo, isHigh ? highRiskLineMat : lineMat);
        scene.add(line);
      }
    });

    // 7. Raycaster for Interactive Node Hover & Selection
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();

    const getIntersectedNode = (e) => {
      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
      raycaster.setFromCamera(mouse, camera);
      const intersects = raycaster.intersectObjects(nodeMeshes);
      return intersects.length > 0 ? intersects[0] : null;
    };

    const handlePointerMove = (e) => {
      const hit = getIntersectedNode(e);
      if (hit) {
        renderer.domElement.style.cursor = "pointer";
        setHoveredNode(hit.object.userData);
      } else {
        renderer.domElement.style.cursor = "grab";
        setHoveredNode(null);
      }
    };

    const handleClick = (e) => {
      const hit = getIntersectedNode(e);
      if (hit) {
        const targetNode = hit.object.userData;
        setSelectedNode(targetNode);
        if (onSelectNode) onSelectNode(targetNode);

        // Fly camera smoothly to target node
        const pos = hit.object.position;
        controls.target.set(pos.x, pos.y, pos.z);
        camera.position.set(pos.x, pos.y + 1, pos.z + 5);
        controls.update();
      }
    };

    renderer.domElement.addEventListener("pointermove", handlePointerMove);
    renderer.domElement.addEventListener("click", handleClick);

    // 8. Render Animation Loop
    let animId;
    let clock = new THREE.Clock();

    const animate = () => {
      animId = requestAnimationFrame(animate);
      const elapsedTime = clock.getElapsedTime();

      // Slow gentle rotation if autoRotate is enabled
      if (autoRotate) {
        scene.rotation.y = elapsedTime * 0.05;
      }

      // Pulse anchor meshes
      nodeMeshes.forEach((mesh) => {
        if (mesh.userData.is_case_anchor) {
          const s = 1.0 + Math.sin(elapsedTime * 3) * 0.08;
          mesh.scale.set(s, s, s);
        }
      });

      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    // 9. Resize Handling
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
      renderer.domElement.removeEventListener("pointermove", handlePointerMove);
      renderer.domElement.removeEventListener("click", handleClick);
      window.removeEventListener("resize", handleResize);
      cancelAnimationFrame(animId);
      if (controls) controls.dispose();
      scene.traverse((obj) => {
        if (obj.geometry) obj.geometry.dispose();
        if (obj.material) {
          if (Array.isArray(obj.material)) {
            obj.material.forEach((m) => m.dispose());
          } else {
            obj.material.dispose();
          }
        }
      });
      if (currentMount.contains(renderer.domElement)) {
        currentMount.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };

  }, [graphData, autoRotate]);

  // Handler to center camera back on anchor
  const handleResetCamera = () => {
    if (cameraRef.current && controlsRef.current) {
      cameraRef.current.position.set(0, 2, 14);
      controlsRef.current.target.set(0, 0, 0);
      controlsRef.current.update();
      if (sceneRef.current) {
        sceneRef.current.rotation.y = 0;
      }
    }
  };

  return (
    <div style={{ width: "100%", height: "420px", position: "relative", borderRadius: "12px", overflow: "hidden", background: "radial-gradient(circle at center, rgba(30, 41, 59, 0.4) 0%, rgba(10, 15, 30, 0.95) 100%)" }}>
      {/* 3D WebGL Canvas */}
      <div ref={mountRef} style={{ width: "100%", height: "100%" }} />

      {/* Floating Viewport Controls */}
      <div style={{
        position: "absolute",
        top: "14px",
        right: "14px",
        display: "flex",
        gap: "8px",
        zIndex: 10
      }}>
        <button
          onClick={() => setAutoRotate(!autoRotate)}
          className="mini-ctrl-btn"
          style={{
            background: autoRotate ? "rgba(6, 182, 212, 0.2)" : "rgba(15, 23, 42, 0.8)",
            border: `1px solid ${autoRotate ? "#06B6D4" : "rgba(255, 255, 255, 0.15)"}`,
            color: autoRotate ? "#06B6D4" : "#94A3B8",
            borderRadius: "6px",
            padding: "5px 10px",
            fontSize: "11px",
            cursor: "pointer",
            backdropFilter: "blur(6px)"
          }}
        >
          {autoRotate ? "⏸ PAUSE ROTATION" : "▶ AUTO-ROTATE"}
        </button>

        <button
          onClick={handleResetCamera}
          className="mini-ctrl-btn"
          style={{
            background: "rgba(15, 23, 42, 0.8)",
            border: "1px solid rgba(255, 255, 255, 0.15)",
            color: "#F8FAFC",
            borderRadius: "6px",
            padding: "5px 10px",
            fontSize: "11px",
            cursor: "pointer",
            backdropFilter: "blur(6px)"
          }}
        >
          🎯 FOCUS ANCHOR
        </button>
      </div>

      {/* Hover / Selected Entity HUD Overlay */}
      {(hoveredNode || selectedNode) && (
        <div style={{
          position: "absolute",
          bottom: "14px",
          left: "14px",
          background: "rgba(15, 23, 42, 0.92)",
          border: `1px solid ${hoveredNode ? (hoveredNode.risk_score >= 80 ? "#EF4444" : "#06B6D4") : "#8B5CF6"}`,
          borderRadius: "8px",
          padding: "10px 16px",
          fontSize: "12px",
          backdropFilter: "blur(12px)",
          boxShadow: "0 8px 32px rgba(0, 0, 0, 0.5)",
          maxWidth: "340px",
          zIndex: 10
        }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "10px", marginBottom: "4px" }}>
            <span style={{ fontSize: "10px", fontWeight: 700, letterSpacing: "0.05em", color: "#94A3B8", textTransform: "uppercase" }}>
              {hoveredNode ? "HOVERED ENTITY" : "SELECTED ENTITY"} ({hoveredNode ? hoveredNode.type : selectedNode.type})
            </span>
            <span style={{
              fontSize: "10px",
              fontWeight: 800,
              padding: "2px 6px",
              borderRadius: "4px",
              background: (hoveredNode || selectedNode).risk_score >= 80 ? "rgba(239, 68, 68, 0.2)" : "rgba(16, 185, 129, 0.2)",
              color: (hoveredNode || selectedNode).risk_score >= 80 ? "#EF4444" : "#10B981"
            }}>
              {(hoveredNode || selectedNode).risk_level || `${(hoveredNode || selectedNode).risk_score}% RISK`}
            </span>
          </div>

          <div style={{ fontSize: "13px", fontWeight: 700, color: "#F8FAFC", marginBottom: "4px" }}>
            {(hoveredNode || selectedNode).label}
          </div>

          <div style={{ fontSize: "11px", color: "#94A3B8" }}>
            ID: <code style={{ color: "#06B6D4" }}>{(hoveredNode || selectedNode).id}</code>
            {(hoveredNode || selectedNode).cluster_id && (
              <span style={{ marginLeft: "8px", color: "#A78BFA" }}>
                Ring: <b>{(hoveredNode || selectedNode).cluster_id}</b>
              </span>
            )}
          </div>
        </div>
      )}

      {/* Graph Legend */}
      <div style={{
        position: "absolute",
        bottom: "14px",
        right: "14px",
        background: "rgba(15, 23, 42, 0.85)",
        border: "1px solid rgba(255, 255, 255, 0.1)",
        borderRadius: "8px",
        padding: "8px 12px",
        fontSize: "10px",
        backdropFilter: "blur(8px)",
        display: "flex",
        flexDirection: "column",
        gap: "4px",
        color: "#94A3B8"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#FF0055", display: "inline-block" }} />
          <span>Case Anchor / Transaction</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#EF4444", display: "inline-block" }} />
          <span>High-Risk / Compromised</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#8B5CF6", display: "inline-block" }} />
          <span>Mule Ring Aggregator</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#10B981", display: "inline-block" }} />
          <span>Verified Legit / Low Risk</span>
        </div>
      </div>
    </div>
  );
}
