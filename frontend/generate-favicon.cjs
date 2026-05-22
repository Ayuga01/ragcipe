const { Resvg } = require('@resvg/resvg-js');
const fs = require('fs');
const path = require('path');


const svg = `
<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
  <rect width="512" height="512" rx="100" fill="#f5b942"/>
  <g transform="translate(16, 16) scale(20)">
    <path d="M17 21a1 1 0 0 0 1-1v-5.35c0-.457.316-.844.727-1.041a4 4 0 0 0-2.134-7.589v-.02a4 4 0 0 0-7.186 0v.02a4 4 0 0 0-2.134 7.589c.411.197.727.584.727 1.041V20a1 1 0 0 0 1 1Z" fill="none" stroke="#12121a" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M6 17h12" fill="none" stroke="#12121a" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
  </g>
</svg>
`;

async function generate() {
  const publicDir = path.join(__dirname, 'public');
  
  // Clean old favicon if any
  try {
    const oldViteSvg = path.join(publicDir, 'vite.svg');
    if (fs.existsSync(oldViteSvg)) fs.unlinkSync(oldViteSvg);
  } catch (err) {}

  const renderPng = (size) => {
    const resvg = new Resvg(svg, {
      fitTo: { mode: 'width', value: size },
    });
    return resvg.render().asPng();
  };

  fs.writeFileSync(path.join(publicDir, 'favicon-16x16.png'), renderPng(16));
  fs.writeFileSync(path.join(publicDir, 'favicon-32x32.png'), renderPng(32));
  fs.writeFileSync(path.join(publicDir, 'apple-touch-icon.png'), renderPng(180));

  fs.writeFileSync(path.join(publicDir, 'favicon.ico'), renderPng(32));

  console.log('Favicon generation complete.');
}

generate().catch(console.error);
