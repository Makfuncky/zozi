const fs=require('fs');
const path = require('path');
const lines=fs.readFileSync(path.join(__dirname, 'web_app', 'src', 'components', 'Header.tsx'),'utf8').split(/\r?\n/);
for(let i=250;i<300;i++){console.log((i+1)+': '+lines[i]);}
