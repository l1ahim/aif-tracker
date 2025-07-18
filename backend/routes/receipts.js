const express = require('express');
const router = express.Router();
const Receipt = require('../models/Receipt');

// POST /receipts/upload
router.post('/upload', async (req, res) => {
    try {
        const { filename, amount, ...otherFields } = req.body;

        // Check for duplicate by filename
        const existing = await Receipt.findOne({ filename });
        if (existing) {
            return res.status(409).json({ message: 'Receipt already uploaded.' });
        }

        // Save new receipt
        const newReceipt = new Receipt({ filename, amount, ...otherFields });
        await newReceipt.save();

        // Calculate total spent for the current month
        const now = new Date();
        const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
        const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0, 23, 59, 59, 999);

        const monthlyReceipts = await Receipt.find({
            createdAt: { $gte: firstDay, $lte: lastDay }
        });

        const totalSpentThisMonth = monthlyReceipts.reduce((sum, r) => sum + (r.amount || 0), 0);

        res.status(201).json({ message: 'Receipt uploaded.', totalSpentThisMonth });
    } catch (err) {
        console.error(err);
        // Handle duplicate key error from unique index
        if (err.code === 11000) {
            return res.status(409).json({ message: 'Receipt already uploaded.' });
        }
        res.status(500).json({ message: 'Server error.', error: err.message });
    }
});

module.exports = router;