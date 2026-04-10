/**
 * FaceMeshAR Component
 * AR try-on component using MediaPipe Face Mesh for face tracking
 * Overlays earrings on detected ear positions
 */
import React, { useRef, useEffect, useState, useCallback } from 'react';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { FaceMesh } from '@mediapipe/face_mesh';
import { Camera } from '@mediapipe/camera_utils';

// Face mesh landmarks for ear positions (approximate)
const LEFT_EAR_LANDMARKS = [127, 128, 129, 130, 131, 132, 232, 233, 234, 235, 236];
const RIGHT_EAR_LANDMARKS = [356, 357, 358, 359, 360, 361, 452, 453, 454, 455, 456];

export default function FaceMeshAR({
  jewelry,
  jewelryType,
  onScreenshot,
  isActive
}) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const overlayCanvasRef = useRef(null);
  const sceneRef = useRef(null);
  const faceMeshRef = useRef(null);
  const cameraRef = useRef(null);
  const earringMeshRef = useRef(null);
  const animationFrameRef = useRef(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [fps, setFps] = useState(0);
  const lastFrameTime = useRef(Date.now());
  const frameCount = useRef(0);

  // Initialize Three.js scene
  useEffect(() => {
    if (!canvasRef.current || !isActive) return;

    const canvas = canvasRef.current;
    const scene = new THREE.Scene();
    sceneRef.current = scene;

    // Camera for 3D rendering
    const camera = new THREE.PerspectiveCamera(
      75,
      canvas.clientWidth / canvas.clientHeight,
      0.1,
      1000
    );
    camera.position.z = 500;
    cameraRef.current = camera;

    // Renderer
    const renderer = new THREE.WebGLRenderer({
      canvas,
      alpha: true,
      antialias: true
    });
    renderer.setSize(canvas.clientWidth, canvas.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
    directionalLight.position.set(0, 100, 100);
    scene.add(directionalLight);

    // Handle resize
    const handleResize = () => {
      if (canvas && cameraRef.current && sceneRef.current) {
        cameraRef.current.aspect = canvas.clientWidth / canvas.clientHeight;
        cameraRef.current.updateProjectionMatrix();
        renderer.setSize(canvas.clientWidth, canvas.clientHeight);
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      renderer.dispose();
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [isActive]);

  // Load 3D model for jewelry
  const loadJewelryModel = useCallback(async (modelUrl) => {
    if (!sceneRef.current || !modelUrl) return;

    setIsLoading(true);
    setError(null);

    try {
      // Remove existing earring mesh
      if (earringMeshRef.current) {
        sceneRef.current.remove(earringMeshRef.current);
        earringMeshRef.current = null;
      }

      const loader = new GLTFLoader();
      const gltf = await new Promise((resolve, reject) => {
        loader.load(modelUrl, resolve, undefined, reject);
      });

      const model = gltf.scene;

      // Scale and position the model
      model.scale.set(50, 50, 50);
      model.position.set(0, 0, 0);

      // Enable shadows
      model.traverse((node) => {
        if (node.isMesh) {
          node.castShadow = true;
          node.receiveShadow = true;
        }
      });

      earringMeshRef.current = model;
      sceneRef.current.add(model);

      setIsLoading(false);
    } catch (err) {
      console.error('Failed to load 3D model:', err);
      setError('Failed to load 3D model. Using fallback visualization.');
      setIsLoading(false);

      // Create fallback geometry
      createFallbackEarring();
    }
  }, []);

  // Create fallback earring geometry if model fails to load
  const createFallbackEarring = useCallback(() => {
    if (!sceneRef.current) return;

    const geometry = new THREE.SphereGeometry(15, 32, 32);
    const material = new THREE.MeshStandardMaterial({
      color: 0xffd700,
      metalness: 0.8,
      roughness: 0.2,
    });

    const sphere = new THREE.Mesh(geometry, material);
    sphere.scale.set(1, 1, 1);

    earringMeshRef.current = sphere;
    sceneRef.current.add(sphere);
  }, []);

  // Initialize MediaPipe Face Mesh
  useEffect(() => {
    if (!videoRef.current || !overlayCanvasRef.current || !isActive) return;

    const video = videoRef.current;
    const overlayCanvas = overlayCanvasRef.current;
    const overlayCtx = overlayCanvas.getContext('2d');

    const faceMesh = new FaceMesh({
      locateFile: (file) => {
        return `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`;
      }
    });

    faceMesh.setOptions({
      maxNumFaces: 1,
      refineLandmarks: true,
      minDetectionConfidence: 0.5,
      minTrackingConfidence: 0.5
    });

    faceMesh.onResults((results) => {
      // Update FPS counter
      frameCount.current++;
      const now = Date.now();
      if (now - lastFrameTime.current >= 1000) {
        setFps(frameCount.current);
        frameCount.current = 0;
        lastFrameTime.current = now;
      }

      // Clear overlay canvas
      overlayCtx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);

      if (results.multiFaceLandmarks && results.multiFaceLandmarks.length > 0) {
        const landmarks = results.multiFaceLandmarks[0];

        // Draw face landmarks for debugging
        // drawLandmarks(overlayCtx, landmarks);

        // Get ear positions
        const leftEarPos = getEarPosition(landmarks, LEFT_EAR_LANDMARKS, video.videoWidth, video.videoHeight);
        const rightEarPos = getEarPosition(landmarks, RIGHT_EAR_LANDMARKS, video.videoWidth, video.videoHeight);

        // Update earring positions in 3D scene
        updateEarringPositions(leftEarPos, rightEarPos);
      }
    });

    faceMeshRef.current = faceMesh;

    // Start camera
    const startCamera = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: {
            width: { ideal: 1280 },
            height: { ideal: 720 },
            facingMode: 'user'
          }
        });

        video.srcObject = stream;
        await new Promise((resolve) => {
          video.onloadedmetadata = () => {
            video.play();
            resolve();
          };
        });

        overlayCanvas.width = video.videoWidth;
        overlayCanvas.height = video.videoHeight;

        // Start face detection
        const camera = new Camera(video, {
          onFrame: async () => {
            await faceMesh.send({ image: video });
          },
          width: video.videoWidth,
          height: video.videoHeight
        });
        camera.start();
      } catch (err) {
        console.error('Camera error:', err);
        setError('Failed to access camera. Please grant camera permissions.');
      }
    };

    startCamera();

    return () => {
      if (video.srcObject) {
        video.srcObject.getTracks().forEach(track => track.stop());
      }
      faceMesh.close();
    };
  }, [isActive]);

  // Load jewelry model when selection changes
  useEffect(() => {
    if (!jewelry || !isActive) return;

    const modelUrl = jewelry.model_url || '/models/default-earring.glb';
    loadJewelryModel(modelUrl);
  }, [jewelry, isActive, loadJewelryModel]);

  // Calculate ear position from face landmarks
  const getEarPosition = (landmarks, earIndices, videoWidth, videoHeight) => {
    let x = 0, y = 0, z = 0;
    let count = 0;

    earIndices.forEach(index => {
      if (landmarks[index]) {
        x += landmarks[index].x;
        y += landmarks[index].y;
        z += landmarks[index].z;
        count++;
      }
    });

    if (count === 0) return { x: 0, y: 0, z: 0 };

    return {
      x: (x / count) * videoWidth,
      y: (y / count) * videoHeight,
      z: z / count
    };
  };

  // Update earring mesh positions based on face tracking
  const updateEarringPositions = (leftEar, rightEar) => {
    if (!earringMeshRef.current || !sceneRef.current || !cameraRef.current) return;

    // Convert 2D screen coordinates to 3D world coordinates
    const vector = new THREE.Vector3();

    // For simplicity, position earrings based on landmark positions
    // In a production system, you'd use proper 3D face mesh alignment

    const leftEarX = (leftEar.x / overlayCanvasRef.current.width - 0.5) * 200;
    const leftEarY = -(leftEar.y / overlayCanvasRef.current.height - 0.5) * 200;
    const rightEarX = (rightEar.x / overlayCanvasRef.current.width - 0.5) * 200;
    const rightEarY = -(rightEar.y / overlayCanvasRef.current.height - 0.5) * 200;

    // Position the earring mesh (simplified - in production, use two meshes)
    earringMeshRef.current.position.set(
      (leftEarX + rightEarX) / 2,
      (leftEarY + rightEarY) / 2,
      -50 + (leftEar.z + rightEar.z) * 50
    );

    // Rotate to face the camera
    earringMeshRef.current.lookAt(cameraRef.current.position);
  };

  // Draw landmarks for debugging
  const drawLandmarks = (ctx, landmarks, videoWidth, videoHeight) => {
    ctx.strokeStyle = '#00FF00';
    ctx.lineWidth = 1;

    landmarks.forEach((landmark, index) => {
      const x = landmark.x * videoWidth;
      const y = landmark.y * videoHeight;

      ctx.beginPath();
      ctx.arc(x, y, 2, 0, 2 * Math.PI);
      ctx.stroke();
    });
  };

  // Capture screenshot
  const captureScreenshot = useCallback(() => {
    if (!canvasRef.current || !videoRef.current) return null;

    const canvas = document.createElement('canvas');
    const video = videoRef.current;
    const overlay = overlayCanvasRef.current;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');

    // Draw video frame
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Draw 3D overlay (earrings)
    if (canvasRef.current) {
      ctx.drawImage(canvasRef.current, 0, 0, canvas.width, canvas.height);
    }

    return canvas.toDataURL('image/png');
  }, []);

  // Expose screenshot function to parent
  useEffect(() => {
    if (onScreenshot) {
      onScreenshot(() => captureScreenshot());
    }
  }, [onScreenshot, captureScreenshot]);

  return (
    <div style={styles.container}>
      {/* Video element for webcam */}
      <video
        ref={videoRef}
        style={styles.video}
        playsInline
        muted
      />

      {/* MediaPipe overlay canvas for face detection visualization */}
      <canvas
        ref={overlayCanvasRef}
        style={styles.overlayCanvas}
      />

      {/* Three.js canvas for 3D jewelry rendering */}
      <canvas
        ref={canvasRef}
        style={styles.threeCanvas}
      />

      {/* Loading indicator */}
      {isLoading && (
        <div style={styles.loadingOverlay}>
          <div style={styles.spinner}></div>
          <span>Loading jewelry...</span>
        </div>
      )}

      {/* Error message */}
      {error && (
        <div style={styles.errorOverlay}>
          {error}
        </div>
      )}

      {/* FPS counter */}
      <div style={styles.fpsCounter}>
        FPS: {fps}
      </div>
    </div>
  );
}

const styles = {
  container: {
    position: 'relative',
    width: '100%',
    height: '100%',
    minHeight: '500px',
    background: '#000',
    borderRadius: '8px',
    overflow: 'hidden',
  },
  video: {
    position: 'absolute',
    width: '100%',
    height: '100%',
    objectFit: 'cover',
    transform: 'scaleX(-1)', // Mirror effect
  },
  overlayCanvas: {
    position: 'absolute',
    width: '100%',
    height: '100%',
    transform: 'scaleX(-1)',
    pointerEvents: 'none',
  },
  threeCanvas: {
    position: 'absolute',
    width: '100%',
    height: '100%',
    transform: 'scaleX(-1)',
    pointerEvents: 'none',
  },
  loadingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'rgba(0, 0, 0, 0.5)',
    color: '#fff',
    zIndex: 10,
  },
  spinner: {
    width: '40px',
    height: '40px',
    border: '4px solid rgba(255, 255, 255, 0.3)',
    borderTopColor: '#fff',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
    marginBottom: '10px',
  },
  errorOverlay: {
    position: 'absolute',
    bottom: '20px',
    left: '50%',
    transform: 'translateX(-50%)',
    background: 'rgba(220, 38, 38, 0.9)',
    color: '#fff',
    padding: '10px 20px',
    borderRadius: '4px',
    fontSize: '14px',
    zIndex: 10,
  },
  fpsCounter: {
    position: 'absolute',
    top: '10px',
    right: '10px',
    background: 'rgba(0, 0, 0, 0.7)',
    color: '#00FF00',
    padding: '4px 8px',
    borderRadius: '4px',
    fontSize: '12px',
    fontFamily: 'monospace',
    zIndex: 10,
  },
};
