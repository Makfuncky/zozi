const fs=require('fs');
const path = require('path');
const code=fs.readFileSync(path.join(__dirname, 'web_app', 'src', 'components', 'Header.tsx'),'utf8');
let open=0, close=0;
const lines=code.split(/\r?\n/);
lines.forEach((l,i)=>{
 if(l.match(/<div[\s>]/)) open++;
 if(l.match(/<\/div>/)) close++;
});
console.log('open',open,'close',close,'diff',open-close);
