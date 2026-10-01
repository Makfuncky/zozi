const fs = require('fs');
const path = require('path');
const glob = require('glob');

const base = __dirname;

glob.sync('src/**/*.tsx', { cwd: base }).forEach(file => {
  const full = path.join(base, file);
  let text = fs.readFileSync(full, 'utf8');
  const orig = text;
  text = text.replace(/bg-linear-to-r/g, 'bg-gradient-to-r')
             .replace(/bg-linear-to-br/g, 'bg-gradient-to-br');
  text = text.replace(/from-\(\-\-zozi-([^\)]+)\)/g, 'from-zozi-$1');
  text = text.replace(/to-\(\-\-zozi-([^\)]+)\)/g, 'to-zozi-$1');
  text = text.replace(/via-\(\-\-zozi-([^\)]+)\)/g, 'via-zozi-$1');
  text = text.replace(/bg-\(\-\-zozi-([^\)]+)\)/g, 'bg-zozi-$1');
  text = text.replace(/text-\(\-\-zozi-([^\)]+)\)/g, 'text-zozi-$1');
  text = text.replace(/focus-visible:ring-\(\-\-zozi-([^\)]+)\)/g, 'focus-visible:ring-zozi-$1');
  text = text.replace(/focus:border-\(\-\-zozi-([^\)]+)\)/g, 'focus:border-zozi-$1');
  text = text.replace(/border-\(\-\-zozi-([^\)]+)\)/g, 'border-zozi-$1');
  text = text.replace(/to-\(\-\-background-secondary\)/g, 'to-background-secondary');
  text = text.replace(/text-\(\-\-foreground-secondary\)/g, 'text-foreground-secondary');
  text = text.replace(/from-\(\-\-background\)/g, 'from-background-luxury');
  text = text.replace(/via-\(\-\-background-luxury\)/g, 'via-background-luxury');
  text = text.replace(/focus:ring-\(\-\-zozi-primary\)/g, 'focus:ring-zozi-primary');
  if (text !== orig) {
    fs.writeFileSync(full, text, 'utf8');
    console.log('patched', file);
  }
});
