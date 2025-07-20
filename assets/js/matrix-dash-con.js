/* Matrix Dash - lluvia continua detrás del contenido */
(function () {

  // Selector de contenedor principal (ajusta si tu site usa otro)
  const container =
    document.querySelector('.page-content') ||
    document.querySelector('.site-content') ||
    document.querySelector('main') ||
    document.body;

  // Crea canvas
  let canvas = document.createElement('canvas');
  canvas.id = 'matrix-overlay';
  container.style.position = 'relative';
  canvas.style.position = 'absolute';
  canvas.style.top = 0;
  canvas.style.left = 0;
  canvas.style.width = '100%';
  canvas.style.height = '100%';
  canvas.style.pointerEvents = 'none'; // <- no bloquea clics
  container.prepend(canvas);

  const ctx = canvas.getContext('2d');

  // Config
  const FONT_SIZE = 14;            // tamaño del caracter
  const COLOR_BASE = [0, 255, 0];  // verde Matrix
  const ALPHA_MIN = 0.45;          // transparencia mínima
  const ALPHA_MAX = 0.85;          // transparencia máxima
  const SPEED_MIN = 0.1;           // píxeles por frame (base)
  const SPEED_MAX = 1;

  const chars = "アァイィウヴエェオカガキギクグケゲコゴサザシジスズセゼソゾタダチッヂヅテデトドナニヌネノABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
  const pool = chars.split("");

  let columns = 0;
  let drops = [];   // array de objetos {y,speed,alpha}

  function measureContainer() {
    const rect = container.getBoundingClientRect();
    const height = container.scrollHeight; // altura real del contenido
    const width = rect.width;
    return { width, height };
  }

  function resize() {
    const { width, height } = measureContainer();
    canvas.width = width;
    canvas.height = height;

    columns = Math.floor(width / FONT_SIZE);
    drops = new Array(columns).fill(null).map(() => ({
      // arranca por arriba en posiciones aleatorias negativas
      y: Math.random() * -height * 0.25,
      speed: SPEED_MIN + Math.random() * (SPEED_MAX - SPEED_MIN),
      alpha: ALPHA_MIN + Math.random() * (ALPHA_MAX - ALPHA_MIN)
    }));
  }

  function drawFrame() {
    // Limpio transparente: NO borra fondo Dash
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.font = FONT_SIZE + "px monospace";

    for (let i = 0; i < columns; i++) {
      const d = drops[i];
      const ch = pool[(Math.random() * pool.length) | 0];
      ctx.fillStyle = `rgba(${COLOR_BASE[0]},${COLOR_BASE[1]},${COLOR_BASE[2]},${d.alpha})`;
      ctx.fillText(ch, i * FONT_SIZE, d.y);

      d.y += d.speed * 3; // velocidad vertical

      // REINICIO SIEMPRE al salir del canvas (antes era random y se "morían")
      if (d.y > canvas.height) {
        d.y = Math.random() * -50; // reinicia arriba (un poco disperso)
        d.speed = SPEED_MIN + Math.random() * (SPEED_MAX - SPEED_MIN);
        d.alpha = ALPHA_MIN + Math.random() * (ALPHA_MAX - ALPHA_MIN);
      }
    }

    requestAnimationFrame(drawFrame);
  }

  // Re-ajusta si el usuario redimensiona
  window.addEventListener('resize', resize);

  // Re-medimos si cambia el contenido (por builds dinámicos)
  const mo = new MutationObserver(() => {
    resize();
  });
  mo.observe(container, { childList: true, subtree: true, characterData: true });

  resize();
  drawFrame();

})();

