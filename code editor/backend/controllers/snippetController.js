const Snippet = require('../models/Snippet');
const { exec } = require('child_process');
const fs = require('fs');

exports.saveSnippet = async (req, res) => {
  const { code, language, userId } = req.body;
  try {
    const snippet = new Snippet({ userId, code, language });
    await snippet.save();
    res.status(201).json(snippet);
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
};

exports.runCode = async (req, res) => {
  const { code, language } = req.body;
  const dockerImage = {
    javascript: 'node:14',
    python: 'python:3.9',
    java: 'openjdk:11',
  }[language];

  const fileName = `code.${language}`;
  fs.writeFileSync(fileName, code);

  const dockerCommand = `docker run --rm -v $(pwd):/app -w /app ${dockerImage} ${language === 'javascript' ? 'node' : language} ${fileName}`;
  exec(dockerCommand, (error, stdout, stderr) => {
    fs.unlinkSync(fileName);
    if (error) return res.status(500).json({ error: stderr });
    res.json({ output: stdout });
  });
};