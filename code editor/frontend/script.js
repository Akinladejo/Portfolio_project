require.config({ paths: { 'vs': 'https://unpkg.com/monaco-editor/min/vs' }});
require(['vs/editor/editor.main'], function() {
  const editorContainer = document.getElementById('editor');
  const editor = monaco.editor.create(editorContainer, {
    value: '// Write your code here\nconsole.log("Hello, World!");',
    language: 'javascript',
    theme: 'vs-dark',
    automaticLayout: false, // Disable automatic layout
  });

  // Manually resize the editor when the window is resized
  window.addEventListener('resize', () => {
    editor.layout();
  });

  const languageSelector = document.getElementById('language');
  languageSelector.addEventListener('change', () => {
    const language = languageSelector.value;
    monaco.editor.setModelLanguage(editor.getModel(), language);
  });

  document.getElementById('run').addEventListener('click', async () => {
    const code = editor.getValue();
    const language = languageSelector.value;
    const outputElement = document.getElementById('output');

    outputElement.textContent = 'Running...';

    try {
      const response = await fetch('/api/snippets/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, language }),
      });
      const result = await response.json();
      outputElement.textContent = result.output || result.error;
    } catch (error) {
      outputElement.textContent = 'Error: Unable to run code.';
    }
  });

  document.getElementById('save').addEventListener('click', async () => {
    const code = editor.getValue();
    const language = languageSelector.value;
    const userId = 'user-id-here'; // Replace with actual user ID from authentication

    try {
      const response = await fetch('/api/snippets/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, language, userId }),
      });
      const result = await response.json();
      alert('Snippet saved successfully!');
      console.log('Snippet saved:', result);
    } catch (error) {
      alert('Error saving snippet.');
    }
  });
});