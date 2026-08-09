const fs=require('fs');
const path = require('path');
const lines=fs.readFileSync(path.join(__dirname, 'web_app', 'src', 'components', 'Header.tsx'),'utf8').split(/\r?\n/);
for(let i=260;i<308;i++){
  console.log((i+1).toString().padStart(3)+": "+lines[i]);
}
