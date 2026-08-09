const fs=require('fs');
const path = require('path');
const lines=fs.readFileSync(path.join(__dirname, 'web_app', 'src', 'components', 'Header.tsx'),'utf8').split(/\r?\n/);
const stack=[];
lines.forEach((l,i)=>{
  if(/<div(\s|>)/.test(l) && !/<\/div>/.test(l) && !/\/\s*>/.test(l)){
    stack.push({line:i+1,text:l.trim()});
  }
  if(/<\/div>/.test(l)){
    if(stack.length>0) stack.pop(); else console.log('extra close at',i+1);
  }
});
console.log('remaining open',stack);
