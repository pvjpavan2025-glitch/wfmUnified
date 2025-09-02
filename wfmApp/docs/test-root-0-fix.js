// Test script to verify root-0 error is fixed
// Run this in browser console on the modelling page

console.log('🧪 Testing BPMN Modeler Safe Operations...');

// Test 1: Check if modeler initializes without root-0 error
setTimeout(() => {
  console.log('📊 Test 1: Checking for modeler initialization...');
  
  // Look for the modeler container
  const modelerContainer = document.querySelector('[data-testid="bpmn-modeler"], .bpmn-container, [class*="bpmn"]');
  if (modelerContainer) {
    console.log('✅ BPMN modeler container found');
  } else {
    console.log('❌ BPMN modeler container not found');
  }
  
  // Check for canvas elements
  const canvasElements = document.querySelectorAll('.djs-container, svg[data-element-id]');
  if (canvasElements.length > 0) {
    console.log('✅ Canvas elements found:', canvasElements.length);
  } else {
    console.log('❌ No canvas elements found');
  }
  
  // Check for any error messages in the DOM
  const errorElements = document.querySelectorAll('[class*="error"], .error, [role="alert"]');
  if (errorElements.length === 0) {
    console.log('✅ No error elements found in DOM');
  } else {
    console.log('⚠️ Error elements found:', errorElements.length);
    errorElements.forEach(el => console.log('Error:', el.textContent));
  }
  
}, 2000);

// Test 2: Try to trigger new diagram creation
setTimeout(() => {
  console.log('📊 Test 2: Testing new diagram creation...');
  
  const newDiagramButton = document.querySelector('button[class*="purple"], button:contains("New Diagram"), [data-testid="new-diagram"]');
  if (newDiagramButton) {
    console.log('✅ New Diagram button found');
    console.log('🎯 Simulating button click...');
    
    // Create a click event
    const clickEvent = new MouseEvent('click', {
      bubbles: true,
      cancelable: true,
      view: window
    });
    
    newDiagramButton.dispatchEvent(clickEvent);
    console.log('🔄 New diagram creation triggered');
    
    // Check for success after delay
    setTimeout(() => {
      const errorMessages = document.querySelectorAll('[class*="error"], .error, [role="alert"]');
      if (errorMessages.length === 0) {
        console.log('✅ No errors after diagram creation');
      } else {
        console.log('❌ Errors found after diagram creation');
      }
    }, 3000);
    
  } else {
    console.log('❌ New Diagram button not found');
  }
  
}, 5000);

// Test 3: Monitor console for errors
const originalError = console.error;
const originalWarn = console.warn;
let errorCount = 0;
let root0ErrorDetected = false;

console.error = function(...args) {
  errorCount++;
  const message = args.join(' ');
  if (message.includes('root-0')) {
    root0ErrorDetected = true;
    console.log('❌ ROOT-0 ERROR DETECTED:', message);
  }
  originalError.apply(console, args);
};

console.warn = function(...args) {
  const message = args.join(' ');
  if (message.includes('root-0')) {
    console.log('⚠️ ROOT-0 WARNING DETECTED:', message);
  }
  originalWarn.apply(console, args);
};

// Report results after 10 seconds
setTimeout(() => {
  console.log('📋 Test Results Summary:');
  console.log(`Total errors detected: ${errorCount}`);
  console.log(`Root-0 error detected: ${root0ErrorDetected ? '❌ YES' : '✅ NO'}`);
  
  if (!root0ErrorDetected && errorCount === 0) {
    console.log('🎉 ALL TESTS PASSED - Root-0 error prevention successful!');
  } else if (!root0ErrorDetected) {
    console.log('✅ Root-0 error prevention successful (but other errors exist)');
  } else {
    console.log('❌ Root-0 error still present - check implementation');
  }
  
  // Restore original console functions
  console.error = originalError;
  console.warn = originalWarn;
  
}, 10000);

console.log('🚀 Test suite started - results in 10 seconds...');
