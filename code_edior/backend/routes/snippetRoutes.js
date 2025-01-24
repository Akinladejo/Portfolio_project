const express = require('express');
const snippetController = require('../controllers/snippetController');

const router = express.Router();
router.post('/save', snippetController.saveSnippet);
router.post('/run', snippetController.runCode);

module.exports = router;