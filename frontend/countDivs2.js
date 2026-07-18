const fs=require('fs');
const lines=fs.readFileSync('src/components/Header.tsx','utf8').split(/\r?\n/);
let open=0, close=0;
lines.forEach((l,i)=>{
 if(/<div(\s|>)/.test(l) && !/\<\/div\>/.test(l)) open++;
 if(/<\/div>/.test(l)) close++;
});
console.log('open',open,'close',close,'diff',open-close);
