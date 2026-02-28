const data = await fetch('./data.json').then((response) => {
  if (!response.ok) throw new Error(`airfoil data request failed: ${response.status}`);
  return response.json();
});
const elements = {
  slider: document.querySelector('#alpha'),
  angle: document.querySelector('#angle'),
  surface: document.querySelector('#surface'),
  lift: document.querySelector('#lift'),
  panelCl: document.querySelector('#panel-cl'),
  nasaCl: document.querySelector('#nasa-cl'),
  regime: document.querySelector('#regime'),
};
const colours = { grid: '#26364d', text: '#94a3b8', panel: '#5eead4', nasa: '#fb923c', thin: '#94a3b8' };
const clamp = (value, low, high) => Math.max(low, Math.min(high, value));
const mix = (a, b, amount) => a.map((value, index) => Math.round(value + (b[index] - value) * amount));
function cpColour(cp) {
  if (cp < 0) {
    const value = mix([30, 41, 78], [94, 234, 212], clamp(-cp / 2.5, 0, 1));
    return `rgb(${value.join(',')})`;
  }
  const value = mix([30, 41, 78], [251, 146, 60], clamp(cp / 1.1, 0, 1));
  return `rgb(${value.join(',')})`;
}
function frame(context, width, height) {
  context.clearRect(0, 0, width, height);
  context.fillStyle = '#0b1424';
  context.fillRect(0, 0, width, height);
}
function drawSurface(index) {
  const canvas = elements.surface;
  const context = canvas.getContext('2d');
  frame(context, canvas.width, canvas.height);
  const margin = 70;
  const scale = canvas.width - 2 * margin;
  const centerY = canvas.height / 2;
  context.strokeStyle = colours.grid;
  context.lineWidth = 1;
  context.beginPath();
  context.moveTo(margin, centerY);
  context.lineTo(canvas.width - margin, centerY);
  context.stroke();
  const pressure = data.pressureCoefficients[index];
  context.lineWidth = 12;
  context.lineCap = 'round';
  for (let point = 0; point < data.geometry.length - 1; point += 1) {
    const start = data.geometry[point];
    const end = data.geometry[point + 1];
    context.strokeStyle = cpColour((pressure[point] + pressure[point + 1]) / 2);
    context.beginPath();
    context.moveTo(margin + start[0] * scale, centerY - start[1] * scale);
    context.lineTo(margin + end[0] * scale, centerY - end[1] * scale);
    context.stroke();
  }
  context.fillStyle = colours.text;
  context.font = '600 20px ui-monospace, monospace';
  context.fillText('Cp −2.5', margin, 34);
  context.fillStyle = '#5eead4';
  context.fillRect(margin + 102, 19, 100, 14);
  context.fillStyle = colours.text;
  context.fillText('0', margin + 224, 34);
  context.fillStyle = '#1e294e';
  context.fillRect(margin + 246, 19, 65, 14);
  context.fillStyle = colours.text;
  context.fillText('+1.1', margin + 334, 34);
  context.fillStyle = '#fb923c';
  context.fillRect(margin + 398, 19, 100, 14);
}
function drawLift(index) {
  const canvas = elements.lift;
  const context = canvas.getContext('2d');
  frame(context, canvas.width, canvas.height);
  const plot = { left: 80, right: canvas.width - 30, top: 25, bottom: canvas.height - 56 };
  const x = (alpha) => plot.left + ((alpha + 6) / 26) * (plot.right - plot.left);
  const y = (cl) => plot.bottom - ((cl + 0.8) / 3.4) * (plot.bottom - plot.top);
  context.font = '600 18px ui-monospace, monospace';
  context.fillStyle = colours.text;
  context.strokeStyle = colours.grid;
  context.lineWidth = 1;
  for (const tick of [-5, 0, 5, 10, 15, 20]) {
    context.beginPath(); context.moveTo(x(tick), plot.top); context.lineTo(x(tick), plot.bottom); context.stroke();
    context.fillText(String(tick), x(tick) - 8, plot.bottom + 30);
  }
  for (const tick of [-0.5, 0, 0.5, 1, 1.5, 2, 2.5]) {
    context.beginPath(); context.moveTo(plot.left, y(tick)); context.lineTo(plot.right, y(tick)); context.stroke();
    context.fillText(tick.toFixed(1), 18, y(tick) + 6);
  }
  function curve(values, colour, dashed = false) {
    context.strokeStyle = colour;
    context.lineWidth = 4;
    context.setLineDash(dashed ? [12, 9] : []);
    context.beginPath();
    data.alphas.forEach((alpha, point) => {
      const action = point ? 'lineTo' : 'moveTo';
      context[action](x(alpha), y(values[point]));
    });
    context.stroke();
    context.setLineDash([]);
  }
  curve(data.thinLift, colours.thin, true);
  curve(data.panelLift, colours.panel);
  context.fillStyle = colours.nasa;
  for (const point of data.nasa) {
    context.beginPath(); context.arc(x(point.alpha), y(point.cl), 6, 0, Math.PI * 2); context.fill();
  }
  const alpha = data.alphas[index];
  context.strokeStyle = '#f8fafc';
  context.lineWidth = 2;
  context.setLineDash([6, 7]);
  context.beginPath(); context.moveTo(x(alpha), plot.top); context.lineTo(x(alpha), plot.bottom); context.stroke();
  context.setLineDash([]);
  context.fillStyle = '#f8fafc';
  context.beginPath(); context.arc(x(alpha), y(data.panelLift[index]), 7, 0, Math.PI * 2); context.fill();
  context.fillStyle = colours.text;
  context.fillText('α [deg]', plot.right - 70, canvas.height - 12);
  context.save(); context.translate(18, plot.top + 30); context.rotate(-Math.PI / 2); context.fillText('Cl', 0, 0); context.restore();
}
function update() {
  const index = Number(elements.slider.value);
  const alpha = data.alphas[index];
  const nearest = data.nasa.reduce((best, point) => Math.abs(point.alpha - alpha) < Math.abs(best.alpha - alpha) ? point : best);
  elements.angle.textContent = `α ${alpha >= 0 ? '+' : ''}${alpha.toFixed(1)}°`;
  elements.panelCl.textContent = data.panelLift[index].toFixed(3);
  elements.nasaCl.textContent = `${nearest.cl.toFixed(3)} @ ${nearest.alpha.toFixed(2)}°`;
  elements.regime.textContent = alpha <= 10.2 ? 'Linear validation' : 'Stall blind spot';
  drawSurface(index);
  drawLift(index);
}
elements.slider.max = data.alphas.length - 1;
elements.slider.addEventListener('input', update);
update();
