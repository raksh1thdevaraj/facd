import '@testing-library/jest-dom';

// Polyfill window.URL.createObjectURL and revokeObjectURL for tests
if (typeof window !== 'undefined') {
  window.URL.createObjectURL = (_blob: Blob | MediaSource) => 'mock-blob-url';

  window.URL.revokeObjectURL = (_url: string) => {};
}

// Polyfill navigator.clipboard
Object.assign(navigator, {
  clipboard: {
    writeText: (_text: string) => Promise.resolve(),
  },
});
