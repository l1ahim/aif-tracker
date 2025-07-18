const mongoose = require('mongoose');

const ReceiptSchema = new mongoose.Schema({
    filename: { type: String, required: true, unique: true },
    amount: { type: Number, required: true },
    // ...other fields...
}, { timestamps: true });

module.exports = mongoose.model('Receipt', ReceiptSchema);