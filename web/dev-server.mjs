import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, resolve } from 'node:path';

const root = resolve('.');
const mime = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
};

const server = createServer(async (req, res) => {
  try {
    const urlPath = req.url === '/' ? '/index.html' : req.url.split('?')[0];
    const safePath = urlPath === '/' ? '/index.html' : urlPath;
    const filePath = join(root, safePath);
    const body = await readFile(filePath);
    res.writeHead(200, { 'content-type': mime[extname(filePath)] || 'text/plain; charset=utf-8' });
    res.end(body);
  } catch {
    try {
      const body = await readFile(join(root, 'index.html'));
      res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
      res.end(body);
    } catch (error) {
      res.writeHead(500, { 'content-type': 'text/plain; charset=utf-8' });
      res.end(String(error));
    }
  }
});

server.listen(5173, () => {
  console.log('followup-radar web running at http://localhost:5173');
});
