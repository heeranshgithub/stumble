// PWA icons with no dependencies: a supersampled rasterizer for the Stumble mark.
// The mark is the product in one glyph: on a stumble-pink ground, a filled ink word-dot beside a
// hollow one. Filled is a word you have; hollow is the one you reached for and missed.
import { deflateSync } from "node:zlib";
import { mkdirSync, writeFileSync } from "node:fs";

const PINK = [0xff, 0x3d, 0x7f];
const INK = [0x1a, 0x12, 0x33];
const PAPER = [0xff, 0xff, 0xff];
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

/** Returns the color at a unit-space point, for a maskable icon (safe zone respected). */
function shade(x, y) {
  // Ground: pink rounded square (full bleed so it also works as a maskable icon).
  if (roundedRect(x, y, 0.5, 0.22) > 0) return null;
  // Filled word-dot, left.
  if (circle(x, y, 0.36, 0.5, 0.135) <= 0) return INK;
  // Hollow word-dot, right: a ring in paper white with an ink core so it reads at 32px too.
  const d = circle(x, y, 0.66, 0.5, 0.135);
  if (d <= 0 && d > -0.05) return PAPER;
  return PINK;
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

mkdirSync("public/icons", { recursive: true });
for (const size of [192, 512]) {
  writeFileSync(`public/icons/icon-${size}.png`, png(size));
}
console.log("wrote public/icons/icon-192.png and icon-512.png");
