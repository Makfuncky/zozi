const fs=require('fs');
const path = require('path');
const code=fs.readFileSync(path.join(__dirname, 'web_app', 'src', 'components', 'Header.tsx'),'utf8');
let paren=0,brace=0,bracket=0;
for(let i=0;i<code.length;i++){const c=code[i];if(c=='(')paren++;if(c==')')paren--; if(c=='{')brace++; if(c=='}')brace--; if(c=='[')bracket++; if(c==']')bracket--; }
console.log('paren',paren,'brace',brace,'bracket',bracket);
