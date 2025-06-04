import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// Get the directory name of the current module
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function runPhaseTest(phaseNumber) {
  const phaseTesterPath = path.join(__dirname, `phases/phase${phaseNumber}.test.js`);
  
  if (!fs.existsSync(phaseTesterPath)) {
    console.error(`No test configuration found for Phase ${phaseNumber}`);
    process.exit(1);
  }
  
  const PhaseTesterModule = await import(phaseTesterPath);
  const PhaseTester = PhaseTesterModule.default;
  const tester = new PhaseTester();
  
  try {
    await tester.setup();
    await tester.runTests();
    await tester.teardown();
    
    tester.printSummary();
    
    if (tester.results.failed > 0) {
      console.error(`Phase ${phaseNumber} tests failed`);
      process.exit(1);
    }
    
    console.log(`Phase ${phaseNumber} tests completed successfully`);
    process.exit(0);
  } catch (error) {
    console.error(`Error running Phase ${phaseNumber} tests:`, error);
    process.exit(1);
  }
}

// Determine which phase to test
const phaseToTest = process.env.DAMIEN_INITIAL_PHASE || '1';
runPhaseTest(parseInt(phaseToTest, 10));