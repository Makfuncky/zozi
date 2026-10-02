import fs from 'fs';
import path from 'path';

export default async (): Promise<void> => {
  console.log('Browser test global teardown starting');

  const reportsDir = path.resolve('reports/run');
  const lastRunPath = path.join(reportsDir, 'last-run.json');
  const resultsPath = path.join(reportsDir, 'results.json');

  try {
    if (fs.existsSync(resultsPath)) {
      fs.mkdirSync(reportsDir, { recursive: true });
      fs.copyFileSync(resultsPath, lastRunPath);
      console.log(`Copied results.json -> last-run.json`);
    } else {
      console.warn(`results.json not found at ${resultsPath}; skipping last-run copy`);
    }
  } catch (err) {
    console.error(`Teardown artifact copy failed: ${err}`);
  }

  console.log('Browser test global teardown complete');
};
