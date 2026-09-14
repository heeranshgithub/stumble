// PWA icons with no dependencies: a supersampled rasterizer for the Stumble mark.
// The mark is one lit sphere on near-black: stumble pink at the highlight, falling to violet in
// shadow. Nothing to decode; it just glows. (Chosen 2026-09-14 from local-docs/.local/icons.)
import { deflateSync } from "node:zlib";
import { mkdirSync, writeFileSync } from "node:fs";

const GROUND = [0x12, 0x0c, 0x22];
// Radial gradient stops, offset 0..1 from the light source.
const STOPS = [
  [0, [0xff, 0xd3, 0xdf]],
  [0.28, [0xff, 0x3d, 0x7f]],
  [0.78, [0x7a, 0x1c, 0x8f]],
  [1, [0x2a, 0x10, 0x50]],
];
const WHITE = [0xff, 0xff, 0xff];
const SS = 4; // supersampling factor per axis

const crcTable = new Int32Array(256).map((_, n) => {
  let c = n;
  for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
  return c;
});
const crc32 = (buf) => {
  let c = -1;
  for (const b of buf) c = crcTable[(c ^ b) & 0xff] ^ (c >>> 8);
  return (c ^ -1) >>> 0;
};
const chunk = (type, data) => {
  const len = Buffer.alloc(4);
  len.writeUInt32BE(data.length);
  const body = Buffer.concat([Buffer.from(type, "ascii"), data]);
  const crc = Buffer.alloc(4);
  crc.writeUInt32BE(crc32(body));
  return Buffer.concat([len, body, crc]);
};

// Signed distance helpers in unit coordinates (0..1).
const roundedRect = (x, y, half, r) => {
  const dx = Math.abs(x - 0.5) - (half - r);
  const dy = Math.abs(y - 0.5) - (half - r);
  return Math.hypot(Math.max(dx, 0), Math.max(dy, 0)) + Math.min(Math.max(dx, dy), 0) - r;
};
const circle = (x, y, cx, cy, r) => Math.hypot(x - cx, y - cy) - r;
const mix = (a, b, t) => a.map((v, i) => v + (b[i] - v) * t);
const gradient = (t) => {
  for (let i = 1; i < STOPS.length; i++) {
    const [t0, c0] = STOPS[i - 1];
    const [t1, c1] = STOPS[i];
    if (t <= t1) return mix(c0, c1, (t - t0) / (t1 - t0));
  }
  return STOPS[STOPS.length - 1][1];
};

/** Returns the color at a unit-space point, for a maskable icon (safe zone respected). */
function shade(x, y) {
  // Ground: near-black rounded square (full bleed so it also works as a maskable icon).
  if (roundedRect(x, y, 0.5, 0.22) > 0) return null;
  // The sphere, lit from upper left.
  if (circle(x, y, 0.5, 0.52, 0.33) > 0) return GROUND;
  let c = gradient(Math.min(1, Math.hypot(x - 0.394, y - 0.375) / 0.528));
  // A soft specular: an ellipse tilted 30°, white at 45%.
  const a = (-30 * Math.PI) / 180;
  const px = x - 0.38, py = y - 0.36;
  const ex = px * Math.cos(a) - py * Math.sin(a), ey = px * Math.sin(a) + py * Math.cos(a);
  if ((ex / 0.1) ** 2 + (ey / 0.06) ** 2 <= 1) c = mix(c, WHITE, 0.45);
  return c;
}

function png(size) {
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(size, 0);
  ihdr.writeUInt32BE(size, 4);
  ihdr[8] = 8; // bit depth
  ihdr[9] = 6; // RGBA
  const rows = [];
  for (let py = 0; py < size; py++) {
    const row = Buffer.alloc(1 + size * 4);
    row[0] = 0;
    for (let px = 0; px < size; px++) {
      let r = 0, g = 0, b = 0, a = 0;
      for (let sy = 0; sy < SS; sy++) {
        for (let sx = 0; sx < SS; sx++) {
          const c = shade((px + (sx + 0.5) / SS) / size, (py + (sy + 0.5) / SS) / size);
          if (c) {
            r += c[0]; g += c[1]; b += c[2]; a += 255;
          }
        }
      }
      const n = SS * SS;
      const alpha = a / n;
      const cov = a ? n * 255 / a : 0; // un-premultiply the covered samples
      const o = 1 + px * 4;
      row[o] = alpha ? Math.round((r / n) * cov) : 0;
      row[o + 1] = alpha ? Math.round((g / n) * cov) : 0;
      row[o + 2] = alpha ? Math.round((b / n) * cov) : 0;
      row[o + 3] = Math.round(alpha);
    }
    rows.push(row);
  }
  return Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    chunk("IHDR", ihdr),
    chunk("IDAT", deflateSync(Buffer.concat(rows))),
    chunk("IEND", Buffer.alloc(0)),
  ]);
}

// An .ico is a 6-byte header, one 16-byte directory entry per image, then the images; PNG-encoded
// entries are valid since Vista and are what every browser reads.
function ico(sizes) {
  const pngs = sizes.map(png);
  const header = Buffer.alloc(6);
  header.writeUInt16LE(1, 2); // type: icon
  header.writeUInt16LE(sizes.length, 4);
  let offset = 6 + 16 * sizes.length;
  const dir = sizes.map((size, i) => {
    const e = Buffer.alloc(16);
    e[0] = size === 256 ? 0 : size;
    e[1] = size === 256 ? 0 : size;
    e.writeUInt16LE(1, 4); // color planes
    e.writeUInt16LE(32, 6); // bits per pixel
    e.writeUInt32LE(pngs[i].length, 8);
    e.writeUInt32LE(offset, 12);
    offset += pngs[i].length;
    return e;
  });
  return Buffer.concat([header, ...dir, ...pngs]);
}

mkdirSync("public/icons", { recursive: true });
for (const size of [192, 512]) {
  writeFileSync(`public/icons/icon-${size}.png`, png(size));
}
writeFileSync("src/app/favicon.ico", ico([16, 32, 48]));
console.log("wrote public/icons/icon-192.png, icon-512.png and src/app/favicon.ico");
