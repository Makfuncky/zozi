const fs=require('fs');
const lines=fs.readFileSync('src/components/Header.tsx','utf8').split(/\r?\n/);
for(let i=250;i<300;i++){console.log((i+1)+': '+lines[i]);}
