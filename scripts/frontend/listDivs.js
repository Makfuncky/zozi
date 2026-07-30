const fs=require('fs');
const path = require('path');
const lines=fs.readFileSync(path.join(__dirname, 'web_app', 'src', 'components', 'Header.tsx'),'utf8').split(/\r?\n/);
lines.forEach((l,i)=>{
 if(l.match(/<div[\s>]/)) console.log('open',i+1,l.trim());
 if(l.match(/<\/div>/)) console.log('close',i+1,l.trim());
});
