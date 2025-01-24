const mongoose = require('mongoose');

const snippetSchema = new mongoose.Schema({
  userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
  code: { type: String, required: true },
  language: { type: String, required: true },
  createdAt: { type: Date, default: Date.now },
  versions: [{ code: String, createdAt: Date }],
});

module.exports = mongoose.model('Snippet', snippetSchema);