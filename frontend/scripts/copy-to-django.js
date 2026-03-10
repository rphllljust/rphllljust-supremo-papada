/**
 * Copia o build do Vite para SUAP/static/react/ e SUAP/static/vue/
 * Rodado após `vite build` via npm run build:django
 */
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const distDir = path.resolve(__dirname, '../dist')

const copies = [
  { src: path.join(distDir, 'react'), dest: path.resolve(__dirname, '../../SUAP/static/react') },
  { src: path.join(distDir, 'vue'),   dest: path.resolve(__dirname, '../../SUAP/static/vue') },
]

function copyDir(srcDir, destDir) {
  fs.mkdirSync(destDir, { recursive: true })
  for (const entry of fs.readdirSync(srcDir, { withFileTypes: true })) {
    const srcPath = path.join(srcDir, entry.name)
    const destPath = path.join(destDir, entry.name)
    if (entry.isDirectory()) {
      copyDir(srcPath, destPath)
    } else {
      fs.copyFileSync(srcPath, destPath)
    }
  }
}

for (const { src, dest } of copies) {
  if (fs.existsSync(src)) {
    console.log(`Copiando ${src} → ${dest}`)
    copyDir(src, dest)
  } else {
    console.warn(`Aviso: diretório não encontrado, pulando: ${src}`)
  }
}
console.log('Build copiado para Django static com sucesso!')
