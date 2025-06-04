import { spawn } from 'child_process';

async function runPhaseTest(phase) {
  return new Promise((resolve, reject) => {
    console.log(`\n============================================`);
    console.log(`Running tests for Phase ${phase}...`);
    console.log(`============================================\n`);
    
    const env = Object.assign({}, process.env, { DAMIEN_INITIAL_PHASE: phase.toString() });
    const testProcess = spawn('node', ['tests/phase-progression.test.js'], { env, stdio: 'inherit' });
    
    testProcess.on('close', (code) => {
      if (code === 0) {
        console.log(`Phase ${phase} tests completed successfully.`);
        resolve();
      } else {
        console.error(`Phase ${phase} tests failed with exit code ${code}.`);
        reject(new Error(`Phase ${phase} tests failed`));
      }
    });
  });
}

async function runAllPhaseTests() {
  try {
    for (let phase = 1; phase <= 6; phase++) {
      await runPhaseTest(phase);
    }
    
    console.log('\n============================================');
    console.log('🎉 All phase tests completed successfully!');
    console.log('============================================\n');
    
    process.exit(0);
  } catch (error) {
    console.error('\n============================================');
    console.error('❌ Phase testing failed:', error.message);
    console.error('============================================\n');
    
    process.exit(1);
  }
}

runAllPhaseTests();