const fs = require('fs');
const parser = require('@babel/parser');
const path = require('path');
const code = fs.readFileSync(path.join(__dirname, 'web_app', 'src', 'components', 'Header.tsx'),'utf8');
try {
  parser.parse(code, {sourceType:'module', plugins:['jsx','typescript']});
  console.log('parsed successfully');
} catch(e){
  console.error('parse error',e.message);
  console.error('loc',e.loc);
}
